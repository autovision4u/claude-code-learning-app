// exercise.js — Exercise submission and feedback display

// Char counter
const input = document.getElementById('exercise-input');
const counter = document.getElementById('char-count');

if (input && counter) {
  input.addEventListener('input', () => {
    const len = input.value.length;
    counter.textContent = len + ' תווים';
    counter.style.color = (typeof MIN_LENGTH !== 'undefined' && len < MIN_LENGTH)
      ? 'var(--warning)' : 'var(--text-light)';
  });
}

function submitExercise() {
  const userInput = document.getElementById('exercise-input').value.trim();
  const btn = document.getElementById('submit-btn');
  const panel = document.getElementById('feedback-panel');
  const errorEl = document.getElementById('feedback-error');
  const contentEl = document.getElementById('feedback-content');
  const completionPanel = document.getElementById('completion-panel');

  if (typeof MIN_LENGTH !== 'undefined' && userInput.length < MIN_LENGTH) {
    alert(`התשובה קצרה מדי. נסה לכתוב לפחות ${MIN_LENGTH} תווים.`);
    return;
  }

  btn.disabled = true;
  btn.textContent = '⏳ קלוד קורא את התשובה שלך...';
  panel.classList.remove('hidden');
  errorEl.classList.add('hidden');
  contentEl.classList.add('hidden');

  fetch('/api/exercise/evaluate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ module_id: MODULE_ID, user_input: userInput })
  })
    .then(r => r.json())
    .then(data => {
      btn.disabled = false;
      btn.textContent = 'שלח שוב';

      if (data.error) {
        errorEl.textContent = data.error;
        errorEl.classList.remove('hidden');
        return;
      }

      document.getElementById('fb-worked').textContent = data.worked_well || '';
      document.getElementById('fb-improve').textContent = data.improve || '';
      document.getElementById('fb-example').textContent = data.improved_example || '';
      contentEl.classList.remove('hidden');

      // Show completion
      if (completionPanel) {
        completionPanel.classList.remove('hidden');
      }

      panel.scrollIntoView({ behavior: 'smooth' });
    })
    .catch(err => {
      btn.disabled = false;
      btn.textContent = 'שלח לבדיקה של קלוד ←';
      errorEl.textContent = 'שגיאה: ' + err.message;
      errorEl.classList.remove('hidden');
    });
}
