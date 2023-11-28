
document.addEventListener('DOMContentLoaded', function() {
  const openPopupButton = document.querySelector('.open-popup');
  const closePopupButton = document.querySelector('.close-popup');
  const popup = document.querySelector('.popup');
  const form = document.getElementById('feedback-form');
  const formStatus = document.querySelector('.form-status');

  openPopupButton.addEventListener('click', function() {
    popup.style.display = 'flex';
    openPopupButton.style.display = 'none';
    history.pushState({ popupIsOpen: true }, '', '#popup');
  });

  closePopupButton.addEventListener('click', function() {
    popup.style.display = 'none';
    openPopupButton.style.display = 'block';
    history.pushState({ popupIsOpen: false }, '', '/');
  });

  const formInputs = ['fullname', 'email', 'phone', 'organization', 'message'];

  formInputs.forEach(inputName => {
    const input = document.getElementById(inputName);
    const savedValue = localStorage.getItem(inputName);

    if (savedValue) {
      input.value = savedValue;
    }

    input.addEventListener('input', function() {
      localStorage.setItem(inputName, input.value);
    });
  });

  form.addEventListener('submit', function(event) {
    event.preventDefault();
    const name_input = document.getElementById('fullname');
    const message_input = document.getElementById('message');

    fetch('https://api.slapform.com/ypAOiDmEL', {
      method: 'POST',
      body: JSON.stringify({ // The data you want submitted and emailed to you
          name: name_input.value,
          message: message_input.value
        })
      })
    .then(function (response) { // This function runs only on success
      console.log('Success!', response);
      formStatus.textContent = 'Form submitted successfully!';
    })
    .catch(function (error) { // This function runs only on error
      console.error('Error:', error);
      formStatus.textContent = 'Error submitting form';
    });
  });

  window.addEventListener('popstate', function(event) {
    if (event.state && event.state.popupIsOpen) {
      popup.style.display = 'flex';
    } else {
      popup.style.display = 'none';
    }
  });
});
