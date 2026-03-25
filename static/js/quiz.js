// quiz.js — Quiz state machine

function submitQuiz() {
  const cards = document.querySelectorAll('.question-card');
  const answers = {};
  let allAnswered = true;

  cards.forEach(card => {
    const qid = card.dataset.qid;
    const selected = card.querySelector('input[type=radio]:checked');
    if (selected) {
      answers[qid] = selected.value;
    } else {
      allAnswered = false;
      card.classList.add('unanswered');
    }
  });

  if (!allAnswered) {
    alert('יש לענות על כל השאלות לפני הבדיקה.');
    return;
  }

  const btn = document.getElementById('submit-quiz');
  btn.disabled = true;
  btn.textContent = '⏳ בודק...';

  fetch('/api/quiz/answer', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ module_id: MODULE_ID, answers })
  })
    .then(r => r.json())
    .then(data => showResults(data, answers))
    .catch(err => {
      btn.disabled = false;
      btn.textContent = 'בדוק תשובות';
      alert('שגיאה: ' + err.message);
    });
}

function showResults(data, answers) {
  const cards = document.querySelectorAll('.question-card');

  // Mark each question
  cards.forEach(card => {
    const qid = card.dataset.qid;
    const result = data.results[qid];
    const feedback = card.querySelector('.question-feedback');
    const hintArea = card.querySelector('.hint-area');

    // Highlight options
    card.querySelectorAll('.option-label').forEach(label => {
      const optId = label.dataset.optId;
      label.classList.remove('correct', 'wrong', 'selected');
      if (optId === result.correct_answer) label.classList.add('correct');
      if (optId === result.user_answer && !result.correct) label.classList.add('wrong');
    });

    // Show explanation
    feedback.textContent = result.explanation;
    feedback.classList.remove('hidden');
    feedback.classList.add(result.correct ? 'feedback-correct' : 'feedback-wrong');

    // Show hint button if wrong
    if (!result.correct) {
      hintArea.classList.remove('hidden');
    }
  });

  // Show score panel
  const scoreEl = document.getElementById('result-score');
  const msgEl = document.getElementById('result-message');
  const exerciseBtn = document.getElementById('exercise-btn');

  scoreEl.textContent = `${data.score} / ${data.total}`;
  scoreEl.className = 'result-score ' + (data.passed ? 'score-pass' : 'score-fail');

  if (data.passed) {
    msgEl.textContent = `🎉 כל הכבוד! עברת את החידון. עכשיו ניתן להמשיך לתרגיל המעשי.`;
    exerciseBtn.classList.remove('hidden');
  } else {
    msgEl.textContent = `קרוב! צריך לפחות ${PASSING_SCORE} תשובות נכונות. נסה שוב לאחר שתחזור על החומר.`;
  }

  document.getElementById('quiz-results').classList.remove('hidden');
  document.getElementById('submit-quiz').style.display = 'none';

  // Scroll to results
  document.getElementById('quiz-results').scrollIntoView({ behavior: 'smooth' });
}

function resetQuiz() {
  // Reset radio buttons
  document.querySelectorAll('input[type=radio]').forEach(r => { r.checked = false; r.disabled = false; });

  // Reset card styles
  document.querySelectorAll('.question-card').forEach(card => {
    card.classList.remove('unanswered');
    card.querySelectorAll('.option-label').forEach(l => l.classList.remove('correct', 'wrong', 'selected'));
    card.querySelector('.question-feedback').classList.add('hidden');
    card.querySelector('.hint-area').classList.add('hidden');
    const hintText = card.querySelector('.hint-text');
    if (hintText) { hintText.textContent = ''; hintText.classList.add('hidden'); }
  });

  // Hide results
  document.getElementById('quiz-results').classList.add('hidden');
  const btn = document.getElementById('submit-quiz');
  btn.style.display = '';
  btn.disabled = false;
  btn.textContent = 'בדוק תשובות';

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function getHint(btn, questionId) {
  const card = btn.closest('.question-card');
  const selected = card.querySelector('input[type=radio]:checked');
  const userAnswer = selected ? selected.value : '';
  const hintText = card.querySelector('.hint-text');

  btn.disabled = true;
  btn.textContent = '⏳ מייצר רמז...';

  fetch('/api/quiz/hint', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ module_id: MODULE_ID, question_id: questionId, user_answer: userAnswer })
  })
    .then(r => r.json())
    .then(data => {
      hintText.textContent = data.hint;
      hintText.classList.remove('hidden');
      btn.textContent = '💡 רמז';
      btn.disabled = false;
    })
    .catch(() => {
      btn.textContent = '💡 רמז';
      btn.disabled = false;
    });
}

// Remove unanswered highlight on selection
document.querySelectorAll('.option-label').forEach(label => {
  label.addEventListener('click', () => {
    label.closest('.question-card').classList.remove('unanswered');
  });
});
