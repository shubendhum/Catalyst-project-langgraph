import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useProjectStore } from '../store/useProjectStore';
import { Plus, Folder, Activity } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';

const Dashboard = () => {
  const navigate = useNavigate();
  const { projects, fetchProjects, createProject } = useProjectStore();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [newProject, setNewProject] = useState({ name: '', description: '' });

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleCreateProject = async () => {
    if (newProject.name.trim()) {
      const project = await createProject(newProject.name, newProject.description);
      if (project) {
        setNewProject({ name: '', description: '' });
        setIsDialogOpen(false);
      }
    }
  };

  return (
    <div data-testid="dashboard-page" style={{ minHeight: '100vh', padding: '48px 24px' }}>
      <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ marginBottom: '48px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '12px' }}>
            <Activity size={48} style={{ color: '#63b3ed' }} />
            <h1
              data-testid="dashboard-title"
              style={{
                fontSize: '56px',
                fontWeight: '700',
                background: 'linear-gradient(135deg, #63b3ed 0%, #90cdf4 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                letterSpacing: '-0.02em',
              }}
            >
              Catalyst
            </h1>
          </div>
          <p style={{ fontSize: '18px', color: '#a0aec0', maxWidth: '600px' }}>
            Multi-agent AI platform for end-to-end application development
          </p>
        </div>

        {/* Create Project Button */}
        <div style={{ marginBottom: '32px' }}>
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button data-testid="create-project-btn" className="btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Plus size={20} />
                New Project
              </Button>
            </DialogTrigger>
            <DialogContent data-testid="create-project-dialog" className="glass-strong" style={{ maxWidth: '500px', padding: '32px' }}>
              <DialogHeader>
                <DialogTitle style={{ fontSize: '24px', marginBottom: '24px' }}>Create New Project</DialogTitle>
                <p style={{ fontSize: '14px', color: '#a0aec0', marginTop: '8px' }}>
                  Start a new AI-powered development project
                </p>
              </DialogHeader>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <div>
                  <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '600' }}>
                    Project Name
                  </label>
                  <Input
                    data-testid="project-name-input"
                    value={newProject.name}
                    onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
                    placeholder="My Awesome App"
                    style={{ width: '100%' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '600' }}>
                    Description
                  </label>
                  <Textarea
                    data-testid="project-description-input"
                    value={newProject.description}
                    onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
                    placeholder="Describe your project..."
                    rows={4}
                    style={{ width: '100%' }}
                  />
                </div>
                <Button
                  data-testid="create-project-submit-btn"
                  onClick={handleCreateProject}
                  className="btn-primary"
                  style={{ width: '100%', marginTop: '8px' }}
                >
                  Create Project
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        {/* Projects Grid */}
        <div data-testid="projects-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '24px' }}>
          {projects.map((project) => (
            <div
              key={project.id}
              data-testid={`project-card-${project.id}`}
              onClick={() => navigate(`/project/${project.id}`)}
              className="card"
              style={{
                cursor: 'pointer',
                padding: '24px',
                position: 'relative',
                overflow: 'hidden',
              }}
            >
              <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '4px', background: 'linear-gradient(90deg, #63b3ed, #90cdf4)' }} />
              
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                <div style={{ padding: '12px', background: 'rgba(99, 179, 237, 0.1)', borderRadius: '12px' }}>
                  <Folder size={24} style={{ color: '#63b3ed' }} />
                </div>
                <div style={{ flex: 1 }}>
                  <h3 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '4px' }}>{project.name}</h3>
                  <span className={`status-badge status-${project.status}`}>{project.status}</span>
                </div>
              </div>
              
              <p style={{ color: '#a0aec0', fontSize: '14px', lineHeight: '1.6' }}>
                {project.description || 'No description provided'}
              </p>
              
              <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid rgba(255, 255, 255, 0.05)', fontSize: '12px', color: '#718096' }}>
                Created {new Date(project.created_at).toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>

        {projects.length === 0 && (
          <div data-testid="empty-state" style={{ textAlign: 'center', padding: '80px 24px' }}>
            <Folder size={80} style={{ color: '#4a5568', margin: '0 auto 24px' }} />
            <h3 style={{ fontSize: '24px', fontWeight: '600', marginBottom: '12px', color: '#a0aec0' }}>
              No projects yet
            </h3>
            <p style={{ color: '#718096', marginBottom: '24px' }}>
              Create your first project to get started with AI-powered development
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;