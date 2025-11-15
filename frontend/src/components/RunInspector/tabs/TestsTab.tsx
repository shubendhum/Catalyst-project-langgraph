import React, { useState } from 'react';
import { RunTest } from '../../../contexts/RunContext.tsx';

interface TestsTabProps {
  run: {
    tests: RunTest[];
  };
}

const TestsTab: React.FC<TestsTabProps> = ({ run }) => {
  const [expandedTest, setExpandedTest] = useState<string | null>(null);

  const toggleExpand = (testId: string) => {
    setExpandedTest(expandedTest === testId ? null : testId);
  };

  if (run.tests.length === 0) {
    return (
      <div className="tests-tab p-6">
        <div className="text-center py-12 text-gray-500">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
          </svg>
          <p className="mt-2 text-sm">No tests run yet</p>
        </div>
      </div>
    );
  }

  const totalTests = run.tests.reduce((sum, test) => sum + (test.summary?.total || 0), 0);
  const passedTests = run.tests.reduce((sum, test) => sum + (test.summary?.passed || 0), 0);
  const failedTests = run.tests.reduce((sum, test) => sum + (test.summary?.failed || 0), 0);

  return (
    <div className="tests-tab p-6 space-y-6">
      {/* Summary */}
      <div className="summary-card bg-white border border-gray-200 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-900 mb-4">Test Summary</h3>
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">{totalTests}</p>
            <p className="text-xs text-gray-500">Total</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-green-600">{passedTests}</p>
            <p className="text-xs text-gray-500">Passed</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-red-600">{failedTests}</p>
            <p className="text-xs text-gray-500">Failed</p>
          </div>
        </div>
      </div>

      {/* Test Results */}
      <div className="space-y-3">
        {run.tests.map((test) => (
          <div key={test.id} className="test-card bg-white border border-gray-200 rounded-lg">
            <div
              className="test-header p-4 cursor-pointer hover:bg-gray-50"
              onClick={() => toggleExpand(test.id)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <TestStatusIcon status={test.status} />
                  <div>
                    <p className="text-sm font-medium text-gray-900">{test.command}</p>
                    {test.summary && (
                      <p className="text-xs text-gray-500 mt-1">
                        {test.summary.passed}/{test.summary.total} passed
                        {test.duration && ` · ${(test.duration / 1000).toFixed(2)}s`}
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {test.exitCode !== undefined && (
                    <span className={`text-xs px-2 py-1 rounded ${
                      test.exitCode === 0 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      Exit {test.exitCode}
                    </span>
                  )}
                  <svg
                    className={`w-4 h-4 text-gray-400 transition-transform ${
                      expandedTest === test.id ? 'transform rotate-180' : ''
                    }`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>
            </div>

            {expandedTest === test.id && (
              <div className="test-details p-4 border-t border-gray-200 bg-gray-50">
                {test.stdout && (
                  <div className="mb-4">
                    <h4 className="text-xs font-semibold text-gray-700 mb-2">Standard Output</h4>
                    <pre className="bg-white p-3 rounded text-xs overflow-x-auto border border-gray-200">
                      <code>{test.stdout}</code>
                    </pre>
                  </div>
                )}
                {test.stderr && (
                  <div>
                    <h4 className="text-xs font-semibold text-gray-700 mb-2">Standard Error</h4>
                    <pre className="bg-red-50 p-3 rounded text-xs overflow-x-auto border border-red-200">
                      <code>{test.stderr}</code>
                    </pre>
                  </div>
                )}
                {test.timestamp && (
                  <p className="text-xs text-gray-500 mt-2">
                    Executed at {new Date(test.timestamp).toLocaleString()}
                  </p>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

function TestStatusIcon({ status }: { status: string }) {
  switch (status) {
    case 'passed':
      return (
        <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
          <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        </div>
      );
    case 'failed':
      return (
        <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center">
          <svg className="w-4 h-4 text-red-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        </div>
      );
    case 'running':
      return (
        <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
          <svg className="w-4 h-4 text-blue-600 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        </div>
      );
    default:
      return (
        <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
          <svg className="w-4 h-4 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
            <circle cx="10" cy="10" r="3" />
          </svg>
        </div>
      );
  }
}

export default TestsTab;