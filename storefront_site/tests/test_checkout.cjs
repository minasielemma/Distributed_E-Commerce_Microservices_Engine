const axios = require('axios');

async function test() {
  try {
    // 1. Login
    const loginRes = await axios.post('http://127.0.0.1/api/auth/token/', {
      username: 'testuser',
      password: 'testpassword123'
    });
    const token = loginRes.data.access;
    console.log("Logged in:", token.substring(0, 20) + "...");

    // 2. Add an item to the cart
    await axios.post('http://127.0.0.1/api/cart/carts/add-item/', {
      product_id: '5e96d865-c627-4121-a31c-5ad7ee95cac3',
      quantity: 1
    }, { headers: { Authorization: `Bearer ${token}` } });
    console.log("Added item to cart");
    
    // 3. Try to checkout
    const orderData = {
        items: [{
            product_id: '5e96d865-c627-4121-a31c-5ad7ee95cac3',
            quantity: 1,
            unit_price: 19.99,
        }],
        shipping_address: {
            id: 'addr123',
            full_name: 'Test User'
        },
        shipping_cost: 0,
        tax_amount: 0
    };
    
    const checkoutRes = await axios.post('http://127.0.0.1/api/orders/create/', orderData, {
      headers: { Authorization: `Bearer ${token}` }
    });
    console.log("Checkout status:", checkoutRes.status);
    console.log("Checkout data:", checkoutRes.data);
    
  } catch(e) {
    console.error("Error:", e.response ? e.response.status : e.message);
    if(e.response) console.error(e.response.data);
  }
}

test();
