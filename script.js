document.getElementById('question-form').addEventListener('submit', function(event) {
    event.preventDefault(); 
    const userAnswer = document.getElementById('answer').value.trim().toLowerCase(); // Приводим ответ к нижнему регистру для удобства
    const correctAnswers = ["ДРОЗОФИЛЫ", "Дрозофилы", "дрозофилы", "ДРОЗОФИЛ", "дрозофил", "Дрозофил", "ДРОЗОФИЛА", "Дрозофила", "дрозофила"];
    if (correctAnswers.includes(userAnswer)) {
        window.location.href = 'video.html';
    } else {
        document.getElementById('error-message').textContent = 'Неправильный ответ! Попробуйте снова. Если не можешь догадаться, загляни в свою любимую книгу "Бесконечное число самых прекрасных форм. 2015", на страницу 91. Если что-то не получатся, напиши мне!';
    }
});



