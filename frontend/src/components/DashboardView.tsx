import { useState } from 'react';
import type { DashboardData, DashboardViewMode, TopicData } from '../types/dashboard';
import { TopicDetailModal } from './TopicDetailModal';
import { SkeletonLoader } from './SkeletonLoader';
import { EmptyState } from './EmptyState';
import { ErrorState } from './ErrorState';
import { NewStudentState } from './NewStudentState';

interface DashboardViewProps {
  data: DashboardData;
  viewMode: DashboardViewMode;
  onNavigateToRoute: (route: any) => void;
  onRetry: () => void;
  onStartDiagnostic: () => void;
  onShowToast: (message: string) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  data,
  viewMode,
  onNavigateToRoute,
  onRetry,
  onStartDiagnostic,
  onShowToast,
}) => {
  const [selectedTopic, setSelectedTopic] = useState<TopicData | null>(null);
  const [tutorInput, setTutorInput] = useState('');

  if (viewMode === 'loading') return <SkeletonLoader />;
  if (viewMode === 'error') return <ErrorState onRetry={onRetry} />;
  if (viewMode === 'new_student') {
    return <NewStudentState studentName={data.student.name} onStartDiagnostic={onStartDiagnostic} />;
  }
  if (viewMode === 'empty') {
    return (
      <EmptyState
        title="No course materials or progress yet"
        message="This course is newly initialized. Ask the instructor or upload course materials to begin learning."
        actionLabel="View Course Materials"
        onAction={() => onNavigateToRoute('materials')}
      />
    );
  }

  const strongCount = data.topics.filter(t => t.status === 'strong').length;
  const developingCount = data.topics.filter(t => t.status === 'developing').length;
  const needsHelpCount = data.topics.filter(t => t.status === 'needs_attention').length;
  const overallMasteryMetric = data.summary.find(m => m.id === 'metric_mastery');

  const handleTutorSubmit = (val: string) => {
    if (!val.trim()) return;
    onShowToast(`Sent prompt to AI Tutor: "${val}"`);
    onNavigateToRoute('tutor');
    setTutorInput('');
  };

  return (
    <div className="new-dashboard-container">
      {/* Top Section */}
      <section className="new-focus-header">
        <div className="new-focus-header-content">
          <h1 className="new-greeting-title">Good morning, {data.student.name.split(' ')[0]}</h1>
          <div className="new-todays-focus">
            <h2 className="new-focus-label">TODAY'S FOCUS</h2>
            <ol className="new-focus-list">
              <li>Review <strong>{data.priorityTopic.focusConcept}</strong></li>
              <li>Practice <strong>{data.continueLearning.currentTopic}</strong></li>
            </ol>
          </div>
        </div>
        <div className="new-focus-action">
          <button className="new-btn-primary-large" onClick={() => onShowToast('Starting Learning Session...')}>
            Start Learning
          </button>
        </div>
      </section>

      <div className="new-dashboard-grid">
        <div className="new-dashboard-left">
          {/* Mastery Summary */}
          <section className="new-card new-mastery-summary-card">
            <div className="new-mastery-overall">
              <span className="new-mastery-value">Overall Mastery {overallMasteryMetric?.value}</span>
              <span className="new-mastery-trend">({overallMasteryMetric?.trend})</span>
            </div>
            <div className="new-mastery-breakdown">
              <span className="new-badge new-badge-strong">Strong {strongCount} topics</span>
              <span className="new-badge new-badge-developing">Developing {developingCount} topics</span>
              <span className="new-badge new-badge-needs-help">Needs Help {needsHelpCount} topic{needsHelpCount === 1 ? '' : 's'}</span>
            </div>
          </section>

          {/* Priority Topic */}
          <section className="new-card new-priority-topic-card">
            <h3 className="new-card-title">Priority: {data.priorityTopic.topicName}</h3>
            <p className="new-card-description">{data.priorityTopic.message}</p>
            <div className="new-card-actions">
              <button 
                className="new-btn-secondary" 
                onClick={() => {
                  const matched = data.topics.find((t) => t.name === data.priorityTopic.topicName);
                  if (matched) setSelectedTopic(matched);
                  else onShowToast(`Opening review materials for ${data.priorityTopic.topicName}...`);
                }}
              >
                Review Topic
              </button>
              <button className="new-btn-primary" onClick={() => onShowToast(`Practicing ${data.priorityTopic.topicName}`)}>
                Practice
              </button>
            </div>
          </section>
          
          {/* Topic Mastery */}
          <section className="new-card new-topic-mastery-card">
            <h3 className="new-card-title">Topic Mastery</h3>
            <div className="new-topic-list-clean">
              {data.topics.map(topic => (
                <div key={topic.id} className="new-topic-row-clean" onClick={() => setSelectedTopic(topic)}>
                  <div className="new-topic-info">
                    <h4 className="new-topic-name">{topic.name}</h4>
                    <span className="new-topic-concepts">{topic.concepts.length} concepts</span>
                  </div>
                  <div className="new-topic-stats">
                    <span className="new-topic-percent">{topic.masteryPercentage}%</span>
                    <span className={`new-topic-status-badge new-status-${topic.status}`}>
                      {topic.status.replace('_', ' ')}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>

        <div className="new-dashboard-right">
          {/* AI Tutor Entry Point */}
          <section className="new-card new-ai-tutor-prominent">
            <div className="new-ai-tutor-label">✦ AI TUTOR</div>
            <h3 className="new-ai-tutor-question">What are you working on today?</h3>
            <div className="new-ai-tutor-input-wrapper">
              <input 
                type="text" 
                className="new-ai-tutor-input"
                placeholder="e.g. Explain gradient descent simply..." 
                value={tutorInput}
                onChange={(e) => setTutorInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleTutorSubmit(e.currentTarget.value);
                  }
                }}
              />
            </div>
            <div className="new-ai-tutor-suggestions">
              <button className="new-prompt-pill" onClick={() => handleTutorSubmit('Explain gradient descent simply')}>
                Explain gradient descent simply
              </button>
              <button className="new-prompt-pill" onClick={() => handleTutorSubmit('Help me practice backprop')}>
                Help me practice backprop
              </button>
              <button className="new-prompt-pill" onClick={() => handleTutorSubmit('Quiz me on Neural Networks')}>
                Quiz me on Neural Networks
              </button>
            </div>
          </section>
        </div>
      </div>

      {selectedTopic && (
        <TopicDetailModal
          topic={selectedTopic}
          onClose={() => setSelectedTopic(null)}
          onActionClick={(actionName) => {
            onShowToast(actionName);
            setSelectedTopic(null);
          }}
        />
      )}
    </div>
  );
};
