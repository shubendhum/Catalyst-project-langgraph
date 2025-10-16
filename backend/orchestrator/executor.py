from agents.planner import PlannerAgent
from agents.architect import ArchitectAgent
from agents.coder import CoderAgent
from agents.tester import TesterAgent
from agents.reviewer import ReviewerAgent
from agents.deployer import DeployerAgent
import asyncio

class TaskExecutor:
    def __init__(self, db, manager):
        self.db = db
        self.manager = manager
        self.planner = PlannerAgent(db, manager)
        self.architect = ArchitectAgent(db, manager)
        self.coder = CoderAgent(db, manager)
        self.tester = TesterAgent(db, manager)
        self.reviewer = ReviewerAgent(db, manager)
        self.deployer = DeployerAgent(db, manager)

    async def execute(self, task_id: str, prompt: str, project_id: str):
        try:
            # Update task status
            await self.db.tasks.update_one(
                {"id": task_id},
                {"$set": {"status": "running"}}
            )

            # Phase 1: Planning
            plan_result = await self.planner.plan(task_id, prompt)
            if plan_result["status"] != "success":
                await self._fail_task(task_id)
                return

            await self._update_graph_state(task_id, "planner", "completed")
            await asyncio.sleep(1)

            # Phase 2: Architecture
            arch_result = await self.architect.design(task_id, plan_result["plan"])
            if arch_result["status"] != "success":
                await self._fail_task(task_id)
                return

            await self._update_graph_state(task_id, "architect", "completed")
            await asyncio.sleep(1)

            # Phase 3: Coding (with retry loop)
            max_retries = 2
            code_result = None
            test_result = None
            test_passed = False
            
            for attempt in range(max_retries):
                if attempt == 0:
                    code_result = await self.coder.code(task_id, arch_result["architecture"])
                else:
                    # Rework based on test feedback
                    code_result = await self.coder.code(task_id, arch_result["architecture"], test_result["test_result"])
                
                if code_result["status"] != "success":
                    await self._fail_task(task_id)
                    return

                await self._update_graph_state(task_id, "coder", "completed")
                await asyncio.sleep(1)

                # Phase 4: Testing
                test_result = await self.tester.test(task_id, code_result["code"])
                if test_result["status"] != "success":
                    await self._fail_task(task_id)
                    return

                await self._update_graph_state(task_id, "tester", "completed")
                
                if test_result["passed"]:
                    test_passed = True
                    break
                else:
                    await self._update_graph_state(task_id, "coder", "reworking")
                    await asyncio.sleep(1)

            if not test_passed:
                await self._fail_task(task_id)
                return

            await asyncio.sleep(1)

            # Phase 5: Review
            review_result = await self.reviewer.review(task_id, code_result["code"], test_result["test_result"])
            if review_result["status"] != "success" or not review_result["approved"]:
                await self._fail_task(task_id)
                return

            await self._update_graph_state(task_id, "reviewer", "completed")
            await asyncio.sleep(1)

            # Phase 6: Deployment
            deploy_result = await self.deployer.deploy(task_id, code_result["code"], project_id)
            if deploy_result["status"] != "success":
                await self._fail_task(task_id)
                return

            await self._update_graph_state(task_id, "deployer", "completed")

            # Mark task as completed
            await self.db.tasks.update_one(
                {"id": task_id},
                {"$set": {"status": "completed", "cost": 0.85}}
            )

        except Exception as e:
            await self._fail_task(task_id)
            raise e

    async def _update_graph_state(self, task_id: str, node: str, status: str):
        task = await self.db.tasks.find_one({"id": task_id})
        graph_state = task.get("graph_state", {})
        graph_state[node] = status
        await self.db.tasks.update_one(
            {"id": task_id},
            {"$set": {"graph_state": graph_state}}
        )

    async def _fail_task(self, task_id: str):
        await self.db.tasks.update_one(
            {"id": task_id},
            {"$set": {"status": "failed"}}
        )