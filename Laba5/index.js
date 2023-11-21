function calculateTotal() {
    var quantity = document.getElementById('quantity').value;
    var selectedProduct = document.getElementById('product');
    var productPrice = selectedProduct.options[selectedProduct.selectedIndex].getAttribute('data-price');
    var totalCost = quantity * productPrice;
    document.getElementById('result').innerHTML = 'Общая стоимость заказа: ' + totalCost.toFixed(2) + ' рублей';
  }