import React, { useState } from 'react';
import { RunFile } from '../../../contexts/RunContext';

interface FilesTabProps {
  run: {
    files: RunFile[];
  };
}

const FilesTab: React.FC<FilesTabProps> = ({ run }) => {
  const [selectedFile, setSelectedFile] = useState<RunFile | null>(null);
  const [viewMode, setViewMode] = useState<'tree' | 'list'>('tree');

  // Build file tree structure
  const buildFileTree = (files: RunFile[]) => {
    const tree: any = {};
    
    files.forEach(file => {
      const parts = file.path.split('/');
      let current = tree;
      
      parts.forEach((part, index) => {
        if (!current[part]) {
          current[part] = index === parts.length - 1 ? file : {};
        }
        current = current[part];
      });
    });
    
    return tree;
  };

  const fileTree = buildFileTree(run.files);

  const renderTree = (node: any, path: string = '') => {
    return Object.entries(node).map(([key, value]) => {
      const currentPath = path ? `${path}/${key}` : key;
      const isFile = value && (value as RunFile).path;
      
      if (isFile) {
        const file = value as RunFile;
        return (
          <div
            key={file.path}
            onClick={() => setSelectedFile(file)}
            className={`file-item cursor-pointer px-3 py-2 hover:bg-gray-100 rounded ${
              selectedFile?.path === file.path ? 'bg-blue-50' : ''
            }`}
          >
            <div className="flex items-center gap-2">
              <FileIcon operation={file.operation} />
              <span className="text-sm text-gray-900">{key}</span>
              <span className={`text-xs px-1.5 py-0.5 rounded ${getOperationBadgeClass(file.operation)}`}>
                {file.operation}
              </span>
            </div>
          </div>
        );
      } else {
        return (
          <details key={currentPath} open>
            <summary className="cursor-pointer px-3 py-2 hover:bg-gray-50 rounded text-sm font-medium text-gray-700">
              📁 {key}
            </summary>
            <div className="ml-4">
              {renderTree(value, currentPath)}
            </div>
          </details>
        );
      }
    });
  };

  return (
    <div className="files-tab flex h-full">
      {/* File Tree */}
      <div className="file-tree w-1/3 border-r border-gray-200 overflow-y-auto p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-gray-900">Files ({run.files.length})</h3>
          <button
            onClick={() => setViewMode(viewMode === 'tree' ? 'list' : 'tree')}
            className="text-xs text-gray-500 hover:text-gray-700"
          >
            {viewMode === 'tree' ? 'List' : 'Tree'}
          </button>
        </div>
        
        {run.files.length === 0 ? (
          <div className="text-center py-8 text-gray-500 text-sm">
            <p>No files modified yet</p>
          </div>
        ) : viewMode === 'tree' ? (
          <div className="space-y-1">{renderTree(fileTree)}</div>
        ) : (
          <div className="space-y-1">
            {run.files.map(file => (
              <div
                key={file.path}
                onClick={() => setSelectedFile(file)}
                className={`file-item cursor-pointer px-3 py-2 hover:bg-gray-100 rounded ${
                  selectedFile?.path === file.path ? 'bg-blue-50' : ''
                }`}
              >
                <div className="flex items-center gap-2">
                  <FileIcon operation={file.operation} />
                  <span className="text-sm text-gray-900 truncate">{file.path}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* File Content / Diff Viewer */}
      <div className="file-content flex-1 overflow-y-auto p-4">
        {selectedFile ? (
          <div>
            <div className="mb-4">
              <h3 className="text-sm font-semibold text-gray-900">{selectedFile.path}</h3>
              <p className="text-xs text-gray-500 mt-1">
                {new Date(selectedFile.timestamp).toLocaleString()} · {selectedFile.operation}
              </p>
            </div>

            {selectedFile.previousContent && selectedFile.content ? (
              /* Show diff */
              <div className="diff-viewer">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="text-xs font-medium text-gray-700 mb-2">Before</h4>
                    <pre className="bg-red-50 p-4 rounded text-xs overflow-x-auto">
                      <code>{selectedFile.previousContent}</code>
                    </pre>
                  </div>
                  <div>
                    <h4 className="text-xs font-medium text-gray-700 mb-2">After</h4>
                    <pre className="bg-green-50 p-4 rounded text-xs overflow-x-auto">
                      <code>{selectedFile.content}</code>
                    </pre>
                  </div>
                </div>
              </div>
            ) : selectedFile.content ? (
              /* Show final content */
              <div>
                <h4 className="text-xs font-medium text-gray-700 mb-2">Content</h4>
                <pre className="bg-gray-50 p-4 rounded text-xs overflow-x-auto border border-gray-200">
                  <code>{selectedFile.content}</code>
                </pre>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500 text-sm">
                <p>No content available</p>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-12 text-gray-500">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="mt-2 text-sm">Select a file to view its content</p>
          </div>
        )}
      </div>
    </div>
  );
};

function FileIcon({ operation }: { operation: string }) {
  switch (operation) {
    case 'create':
      return <span className="text-green-500">+</span>;
    case 'modify':
      return <span className="text-yellow-500">~</span>;
    case 'delete':
      return <span className="text-red-500">-</span>;
    default:
      return <span className="text-gray-500">•</span>;
  }
}

function getOperationBadgeClass(operation: string): string {
  switch (operation) {
    case 'create':
      return 'bg-green-100 text-green-800';
    case 'modify':
      return 'bg-yellow-100 text-yellow-800';
    case 'delete':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

export default FilesTab;