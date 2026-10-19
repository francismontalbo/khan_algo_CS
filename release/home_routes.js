/* Landing-page entry routes. No algorithm or evidence logic is changed. */
(() => {
  'use strict';
  const route = () => {
    const q = new URLSearchParams(window.location.search);
    const view = q.get('open');
    const id = q.get('id');
    if (!view) return;
    try {
      switch (view) {
        case 'lesson':
          if (window.workflowLearning) {
            const lesson = workflowLearning.lessonIds.includes(id) ? id : 'kahn';
            workflowLearning.showLesson(lesson);
          }
          break;
        case 'algorithms': window.workflowLearning?.openAlgorithms(); break;
        case 'simulation': {
          const data = JSON.parse(document.getElementById('simulation-data')?.textContent || '{"engines":[]}');
          const method = data.engines.some(entry => entry.id === id) ? id : 'fifo';
          window.workflowSimulation?.open(method);
          break;
        }
        case 'applications': {
          const profiles = window.workflowApplications?.data?.profiles || [];
          const method = profiles.some(entry => entry.id === id) ? id : 'fifo';
          window.workflowApplications?.open(method);
          break;
        }
        case 'terms':
          if (id && window.workflowReference?.ids?.includes(id)) window.workflowReference.openTerm(id);
          else window.workflowReference?.open(null, 'All');
          break;
        case 'videos': window.workflowLearning?.open(); break;
        default: return;
      }
    } catch (error) {
      // Leave the full guide usable if an optional module is unavailable.
      console.warn('The requested section could not be opened. Use the guide menu.', error);
    }
  };
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => requestAnimationFrame(route), {once:true});
  } else requestAnimationFrame(route);
})();
