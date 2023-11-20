function calculateTotal() {
  var quantity = parseInt(document.getElementById('quantity').value);
  var serviceType = document.querySelector('input[name="serviceType"]:checked').value;
  var serviceOptions = document.getElementById('serviceOptions');
  var propertyCheckbox = document.getElementById('propertyCheckbox');

  var basePrice = 0;

  switch (serviceType) {
    case 'basic':
      basePrice = 10;
      break;
    case 'standard':
      basePrice = 20;
      break;
    case 'premium':
      basePrice = 30;
      break;
  }

  var optionsPrice = serviceOptions.style.display !== 'none' ? parseInt(serviceOptions.value) : 0;
  var propertyPrice = propertyCheckbox.checked ? 5 : 0;

  var totalCost = (basePrice + optionsPrice + propertyPrice) * quantity;

  document.getElementById('result').innerHTML = 'Общая стоимость заказа: ' + totalCost.toFixed(2) + ' рублей';
}

document.addEventListener('DOMContentLoaded', function () {
  var optionsContainer = document.getElementById('optionsContainer');
  var propertyContainer = document.getElementById('propertyContainer');

  document.querySelectorAll('input[name="serviceType"]').forEach(function (radio) {
    radio.addEventListener('change', function () {
      if (this.value === 'basic') {
        optionsContainer.style.display = 'none';
        propertyContainer.style.display = 'none';
      } else if (this.value === 'standard') {
        optionsContainer.style.display = 'block';
        propertyContainer.style.display = 'none';
      } else if (this.value === 'premium') {
        optionsContainer.style.display = 'none';
        propertyContainer.style.display = 'block';
      }
    });
  });
});








function calculateTotal() {
  var quantity = document.getElementById('quantity').value;
  var selectedProduct = document.getElementById('product');
  var productPrice = selectedProduct.options[selectedProduct.selectedIndex].getAttribute('data-price');
  var totalCost = quantity * productPrice;
  document.getElementById('result').innerHTML = 'Общая стоимость заказа: ' + totalCost.toFixed(2) + ' рублей';
}


