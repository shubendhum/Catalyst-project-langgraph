import React, { useState, useMemo } from 'react';
import { RunFile } from '../../../contexts/RunContext';
import ReactDiffViewer from 'react-diff-viewer-continued';
import { ChevronRight, ChevronDown, File, Folder, FolderOpen } from 'lucide-react';

interface FilesTabProps {
  run: {
    files: RunFile[];
  };
}

interface FileTreeNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  children?: FileTreeNode[];
  file?: RunFile;
}

const FilesTab: React.FC<FilesTabProps> = ({ run }) => {
  const [selectedFile, setSelectedFile] = useState<RunFile | null>(null);
  const [expandedDirs, setExpandedDirs] = useState<Set<string>>(new Set(['/']));

  // Build file tree from flat file list
  const fileTree = useMemo(() => {
    const root: FileTreeNode = { name: '/', path: '/', type: 'directory', children: [] };
    
    run.files.forEach(file => {
      const parts = file.path.split('/').filter(Boolean);
      let current = root;
      
      parts.forEach((part, index) => {
        const isLast = index === parts.length - 1;
        const path = '/' + parts.slice(0, index + 1).join('/');
        
        if (!current.children) current.children = [];
        
        let node = current.children.find(n => n.name === part);
        
        if (!node) {
          node = {
            name: part,
            path: path,
            type: isLast ? 'file' : 'directory',
            children: isLast ? undefined : [],
            file: isLast ? file : undefined
          };
          current.children.push(node);
        }
        
        if (!isLast) {
          current = node;
        }
      });
    });
    
    return root;
  }, [run.files]);

  const toggleDirectory = (path: string) => {
    setExpandedDirs(prev => {
      const next = new Set(prev);
      if (next.has(path)) {
        next.delete(path);
      } else {
        next.add(path);
      }
      return next;
    });
  };

  const renderFileTree = (node: FileTreeNode, depth: number = 0): React.ReactNode => {
    if (node.type === 'file' && node.file) {
      return (
        <div
          key={node.path}
          className={`flex items-center gap-2 px-2 py-1.5 cursor-pointer hover:bg-gray-100 rounded transition-colors ${
            selectedFile?.path === node.file.path ? 'bg-blue-50 border-l-2 border-blue-500' : ''
          }`}
          style={{ paddingLeft: `${depth * 16 + 8}px` }}
          onClick={() => setSelectedFile(node.file!)}
        >
          <File size={16} className="text-gray-600 flex-shrink-0" />
          <span className="text-sm text-gray-900 truncate">{node.name}</span>
          <span className={`ml-auto text-xs px-2 py-0.5 rounded ${getOperationBadge(node.file.operation)}`}>
            {node.file.operation}
          </span>
        </div>
      );
    }

    const isExpanded = expandedDirs.has(node.path);

    return (
      <div key={node.path}>
        <div
          className="flex items-center gap-2 px-2 py-1.5 cursor-pointer hover:bg-gray-50 rounded transition-colors"
          style={{ paddingLeft: `${depth * 16 + 8}px` }}
          onClick={() => toggleDirectory(node.path)}
        >
          {isExpanded ? (
            <ChevronDown size={16} className="text-gray-400 flex-shrink-0" />
          ) : (
            <ChevronRight size={16} className="text-gray-400 flex-shrink-0" />
          )}
          {isExpanded ? (
            <FolderOpen size={16} className="text-blue-500 flex-shrink-0" />
          ) : (
            <Folder size={16} className="text-blue-500 flex-shrink-0" />
          )}
          <span className="text-sm font-medium text-gray-900">{node.name}</span>
        </div>
        {isExpanded && node.children && (
          <div>
            {node.children
              .sort((a, b) => {
                if (a.type !== b.type) return a.type === 'directory' ? -1 : 1;
                return a.name.localeCompare(b.name);
              })
              .map(child => renderFileTree(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  if (run.files.length === 0) {
    return (
      <div className="files-tab p-6 flex items-center justify-center h-full">
        <div className="text-center text-gray-500">
          <File size={48} className="mx-auto mb-2 text-gray-400" />
          <p className="text-sm">No files modified in this run</p>
        </div>
      </div>
    );
  }

  return (
    <div className="files-tab flex h-full">
      {/* File Tree Sidebar */}
      <div className="w-64 border-r border-gray-200 overflow-y-auto bg-gray-50">
        <div className="p-3 border-b border-gray-200 bg-white">
          <h4 className="text-sm font-semibold text-gray-900">Files ({run.files.length})</h4>
        </div>
        <div className="p-2">
          {fileTree.children && renderFileTree(fileTree, 0)}
        </div>
      </div>

      {/* Diff Viewer */}
      <div className="flex-1 overflow-y-auto bg-white">
        {selectedFile ? (
          <div className="h-full flex flex-col">
            <div className="p-4 border-b border-gray-200 bg-gray-50">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-semibold text-gray-900">{selectedFile.path}</h4>
                  <p className="text-xs text-gray-500 mt-1">
                    {new Date(selectedFile.timestamp).toLocaleString()} • {getOperationLabel(selectedFile.operation)}
                  </p>
                </div>
                {selectedFile.size && (
                  <span className="text-xs text-gray-500">{formatBytes(selectedFile.size)}</span>
                )}
              </div>
            </div>
            
            <div className="flex-1 overflow-auto">
              {selectedFile.previousContent !== undefined && selectedFile.content !== undefined ? (
                <ReactDiffViewer
                  oldValue={selectedFile.previousContent || ''}
                  newValue={selectedFile.content || ''}
                  splitView={true}
                  showDiffOnly={false}
                  leftTitle="Before"
                  rightTitle="After"
                  styles={{
                    variables: {
                      light: {
                        codeFoldGutterBackground: '#f7fafc',
                        codeFoldBackground: '#f1f5f9',
                        diffViewerBackground: '#ffffff',
                        addedBackground: '#dcfce7',
                        addedGutterBackground: '#bbf7d0',
                        removedBackground: '#fee2e2',
                        removedGutterBackground: '#fecaca',
                        wordAddedBackground: '#86efac',
                        wordRemovedBackground: '#fca5a5',
                      }
                    }
                  }}
                />
              ) : (
                <div className="p-4">
                  <pre className="text-sm font-mono bg-gray-50 p-4 rounded border border-gray-200 overflow-x-auto">
                    {selectedFile.content || '(empty file)'}
                  </pre>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <File size={48} className="mx-auto mb-2 text-gray-400" />
              <p className="text-sm">Select a file to view changes</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

function getOperationBadge(operation: string): string {
  switch (operation) {
    case 'create':
      return 'bg-green-100 text-green-700';
    case 'modify':
      return 'bg-blue-100 text-blue-700';
    case 'delete':
      return 'bg-red-100 text-red-700';
    default:
      return 'bg-gray-100 text-gray-700';
  }
}

function getOperationLabel(operation: string): string {
  switch (operation) {
    case 'create':
      return 'Created';
    case 'modify':
      return 'Modified';
    case 'delete':
      return 'Deleted';
    default:
      return operation;
  }
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

export default FilesTab;