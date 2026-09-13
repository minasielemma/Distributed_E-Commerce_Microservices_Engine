const axios = require('axios');
async function test() {
  try {
    const res = await axios.get('http://127.0.0.1:8000/api/catalog/products/');
    if (res.data.results && res.data.results.length > 0) {
      const pid = res.data.results[0].id;
      const vars = await axios.get(`http://127.0.0.1:8000/api/catalog/variants/?product_id=${pid}`);
      console.log('Variants type:', Array.isArray(vars.data) ? 'array' : 'object', vars.data.results ? 'has results' : 'no results');
    }
  } catch (e) { console.error(e.message); }
}
test();
