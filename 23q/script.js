document.getElementById('question-form').addEventListener('submit', function(event) {
    event.preventDefault(); 
    const userAnswer = document.getElementById('answer').value.trim().toLowerCase(); // Приводим ответ к нижнему регистру для удобства
    const correctAnswers = ["Да", "ДА", "да", "yes", "Yes"];
    if (correctAnswers.includes(userAnswer)) {
        window.location.href = 'video.html';
    } else {
        document.getElementById('error-message').textContent = 'А ну! Упал, отжался';
    }
});



