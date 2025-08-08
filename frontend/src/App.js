import React, { useEffect, useMemo, useState } from "react";
import { BrowserRouter, Routes, Route, Link, useNavigate, useParams } from "react-router-dom";
import axios from "axios";
import "./App.css";

const API_BASE = `${process.env.REACT_APP_BACKEND_URL}/api`;

function useLocalStorage(key, initialValue) {
  const [storedValue, setStoredValue] = useState(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      return initialValue;
    }
  });
  useEffect(() => {
    try {
      window.localStorage.setItem(key, JSON.stringify(storedValue));
    } catch (e) {}
  }, [key, storedValue]);
  return [storedValue, setStoredValue];
}

function Header({ brand }) {
  return (
    <header className="relative bg-zinc-950 text-white">
      <div className="absolute inset-0 opacity-30 bg-[url('https://images.unsplash.com/photo-1482049016688-2d3e1b311543?crop=entropy&cs=srgb&fm=jpg&q=70')] bg-cover bg-center"></div>
      <div className="relative z-10 max-w-6xl mx-auto px-4 py-12">
        <div className="flex items-center justify-between">
          <Link to="/" className="text-2xl font-extrabold tracking-tight">{brand?.name || "Urban Bites"}</Link>
          <nav className="hidden md:flex items-center gap-6 text-sm text-zinc-300">
            <a href="#menu" className="hover:text-white">Menu</a>
            <Link to="/checkout" className="hover:text-white">Checkout</Link>
            <a href="https://emergent.sh" target="_blank" rel="noreferrer" className="hover:text-white">About</a>
          </nav>
        </div>
        <div className="mt-10 max-w-xl">
          <h1 className="text-4xl md:text-5xl font-black leading-tight">Order. Earn. Enjoy.</h1>
          <p className="text-zinc-300 mt-3">Pickup or delivery from our modern kitchen. Fresh burgers and craft coffee.</p>
        </div>
      </div>
    </header>
  );
}

function CategoryTabs({ categories, active, onChange }) {
  return (
    <div className="flex flex-wrap gap-2 mt-6" id="menu">
      {categories.map((c) => (
        <button
          key={c.slug}
          onClick={() => onChange(c.slug)}
          className={`px-3 py-1.5 rounded-full text-sm ${active === c.slug ? "bg-white text-black" : "bg-zinc-800 text-zinc-300 hover:bg-zinc-700"}`}
        >
          {c.name}
        </button>
      ))}
    </div>
  );
}

function ProductCard({ p, onAdd }) {
  const [variantId, setVariantId] = useState(p?.variants?.[0]?.variant_id);
  const [addOns, setAddOns] = useState([]);
  const mainImg = p.images?.[0]?.url;
  const priceWithVariant = useMemo(() => {
    const v = p.variants?.find((x) => x.variant_id === variantId);
    return (p.base_price + (v?.price_delta || 0)).toFixed(2);
  }, [p, variantId]);

  return (
    <div className="bg-zinc-900/60 border border-zinc-800 rounded-2xl p-4 flex flex-col">
      <div className="aspect-[4/3] rounded-xl overflow-hidden bg-zinc-800">
        {mainImg && <img src={mainImg} alt={p.name} className="w-full h-full object-cover" />}
      </div>
      <h3 className="mt-3 text-white font-semibold text-lg">{p.name}</h3>
      <p className="text-sm text-zinc-400 line-clamp-2">{p.description}</p>

      {p.variants?.length > 0 && (
        <div className="mt-3 flex gap-2 flex-wrap">
          {p.variants.map((v) => (
            <button
              key={v.variant_id}
              onClick={() => setVariantId(v.variant_id)}
              className={`px-2.5 py-1 rounded-md text-xs border ${variantId === v.variant_id ? "bg-white text-black border-white" : "border-zinc-700 text-zinc-300 hover:bg-zinc-800"}`}
            >
              {v.name}{v.price_delta ? ` +$${v.price_delta.toFixed(2)}` : ""}
            </button>
          ))}
        </div>
      )}

      {p.add_ons?.length > 0 && (
        <div className="mt-3 grid grid-cols-2 gap-2">
          {p.add_ons.map((a) => (
            <label key={a.add_on_id} className="flex items-center gap-2 text-xs text-zinc-300">
              <input
                type="checkbox"
                checked={addOns.includes(a.add_on_id)}
                onChange={(e) => {
                  setAddOns((prev) => e.target.checked ? [...prev, a.add_on_id] : prev.filter((x) => x !== a.add_on_id));
                }}
              />
              {a.name} {a.price_delta ? `+$${a.price_delta.toFixed(2)}` : ""}
            </label>
          ))}
        </div>
      )}

      <div className="mt-4 flex items-center justify-between">
        <span className="text-white font-semibold">${priceWithVariant}</span>
        <button
          onClick={() => onAdd({ product_id: p.product_id, variant_id: variantId, add_on_ids: addOns, quantity: 1, product: p })}
          className="px-3 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-black font-semibold"
        >
          Add to cart
        </button>
      </div>
    </div>
  );
}

function Cart({ items, onUpdate, onApplyCoupon, totals }) {
  const [code, setCode] = useState("");
  return (
    <div className="bg-zinc-950 text-white">
      <div className="max-w-6xl mx-auto px-4 py-6">
        <h2 className="text-xl font-bold">Your Cart</h2>
        {items.length === 0 ? (
          <p className="text-zinc-400 mt-2">Your cart is empty.</p>
        ) : (
          <div className="mt-4 grid md:grid-cols-3 gap-6">
            <div className="md:col-span-2 space-y-4">
              {items.map((it, idx) => (
                <div key={idx} className="flex gap-4 items-center bg-zinc-900/60 border border-zinc-800 rounded-xl p-3">
                  <img src={it.product.images?.[0]?.url} alt={it.product.name} className="w-20 h-16 object-cover rounded-md" />
                  <div className="flex-1">
                    <div className="font-medium">{it.product.name}</div>
                    <div className="text-xs text-zinc-400">Qty: 
                      <button className="px-2 ml-2 bg-zinc-800 rounded" onClick={() => onUpdate(idx, { quantity: Math.max(1, it.quantity - 1) })}>-</button>
                      <span className="px-2">{it.quantity}</span>
                      <button className="px-2 bg-zinc-800 rounded" onClick={() => onUpdate(idx, { quantity: it.quantity + 1 })}>+</button>
                    </div>
                    {it.add_on_ids?.length > 0 && <div className="text-xs text-zinc-400">Add-ons: {it.add_on_ids.length}</div>}
                  </div>
                  <button className="text-red-400 text-sm" onClick={() => onUpdate(idx, { remove: true })}>Remove</button>
                </div>
              ))}
            </div>
            <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4 h-fit">
              <div className="text-sm text-zinc-300">Subtotal <span className="float-right text-white">${totals.subtotal.toFixed(2)}</span></div>
              <div className="mt-2 flex gap-2">
                <input value={code} onChange={(e) => setCode(e.target.value)} placeholder="Promo code" className="flex-1 bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm" />
                <button onClick={() => onApplyCoupon(code)} className="px-3 py-2 rounded-lg bg-white text-black text-sm font-semibold">Apply</button>
              </div>
              {totals.discount_amount > 0 && <div className="text-sm text-emerald-400 mt-2">Discount -${totals.discount_amount.toFixed(2)}</div>}
              <div className="text-sm text-zinc-300 mt-2">Tax <span className="float-right text-white">${totals.tax_amount.toFixed(2)}</span></div>
              <div className="text-sm text-zinc-300 mt-1">Tip <span className="float-right text-white">${totals.tip_amount.toFixed(2)}</span></div>
              <div className="text-base font-bold mt-3">Total <span className="float-right">${totals.total.toFixed(2)}</span></div>
              <Link to="/checkout" className="mt-4 block text-center px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-black font-semibold">Proceed to Checkout</Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function HomePage() {
  const [config, setConfig] = useState(null);
  const [categories, setCategories] = useState([]);
  const [activeCat, setActiveCat] = useState("burgers");
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useLocalStorage("ub_cart", []);
  const [totals, setTotals] = useState({ subtotal: 0, discount_amount: 0, tax_amount: 0, tip_amount: 0, total: 0 });

  const computeTotals = async (items, code, tip = 0) => {
    const subtotal = items.reduce((acc, it) => {
      const v = it.product.variants?.find((x) => x.variant_id === it.variant_id);
      const addOnsDelta = (it.product.add_ons || []).filter(a => it.add_on_ids?.includes(a.add_on_id)).reduce((s, a) => s + (a.price_delta || 0), 0);
      const unit = (it.product.base_price + (v?.price_delta || 0) + addOnsDelta);
      return acc + unit * it.quantity;
    }, 0);

    let discount_amount = 0;
    if (code) {
      try {
        const resp = await axios.post(`${API_BASE}/cart/validate-coupon`, { code, subtotal });
        discount_amount = resp.data.discount_amount || 0;
      } catch (e) { /* invalid ignored */ }
    }
    const publicCfg = config || (await axios.get(`${API_BASE}/config/public`).then(r => r.data));
    const tax_amount = ((Math.max(0, subtotal - discount_amount)) * (publicCfg.tax_rate || 0));
    const total = Math.max(0, subtotal - discount_amount) + tax_amount + tip;
    setTotals({ subtotal, discount_amount, tax_amount, tip_amount: tip, total });
  };

  useEffect(() => {
    async function init() {
      const cfg = await axios.get(`${API_BASE}/config/public`).then(r => r.data);
      setConfig(cfg);
      const cats = await axios.get(`${API_BASE}/menu/categories`).then(r => r.data);
      setCategories(cats);
      if (cats?.length && !cats.find(c => c.slug === activeCat)) setActiveCat(cats[0].slug);
    }
    init();
  }, []);

  useEffect(() => {
    async function loadProducts() {
      const data = await axios.get(`${API_BASE}/menu/products`, { params: { category: activeCat } }).then(r => r.data);
      setProducts(data);
    }
    if (activeCat) loadProducts();
  }, [activeCat]);

  useEffect(() => { computeTotals(cart); }, [cart]);

  const onAdd = (item) => {
    setCart(prev => [...prev, item]);
  };
  const onUpdate = (idx, patch) => {
    setCart(prev => {
      const next = [...prev];
      if (patch.remove) next.splice(idx, 1);
      else next[idx] = { ...next[idx], ...patch };
      return next;
    });
  };

  const onApplyCoupon = async (code) => {
    await computeTotals(cart, code);
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      <Header brand={config?.brand} />

      <main className="max-w-6xl mx-auto px-4 py-10">
        <div className="flex flex-col md:flex-row gap-10">
          <div className="flex-1">
            <h2 className="text-2xl font-bold">Menu</h2>
            <CategoryTabs categories={categories} active={activeCat} onChange={setActiveCat} />
            <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
              {products.map((p) => (
                <ProductCard key={p.product_id} p={p} onAdd={onAdd} />
              ))}
            </div>
          </div>
          <div className="md:w-96">
            <Cart items={cart} onUpdate={onUpdate} onApplyCoupon={onApplyCoupon} totals={totals} />
          </div>
        </div>
      </main>
    </div>
  );
}

function CheckoutPage() {
  const navigate = useNavigate();
  const [cart, setCart] = useLocalStorage("ub_cart", []);
  const [config, setConfig] = useState(null);
  const [tip, setTip] = useState(0);
  const [form, setForm] = useState({ name: "", email: "", phone: "", fulfillment_type: "pickup", street: "", city: "", postal_code: "" });
  const [pricing, setPricing] = useState({ subtotal: 0, discount_amount: 0, tax_amount: 0, tip_amount: 0, total: 0 });

  const recalc = async () => {
    // Simplified recount. For MVP we reuse logic similar to Home
    const subtotal = cart.reduce((acc, it) => {
      const v = it.product.variants?.find((x) => x.variant_id === it.variant_id);
      const addOnsDelta = (it.product.add_ons || []).filter(a => it.add_on_ids?.includes(a.add_on_id)).reduce((s, a) => s + (a.price_delta || 0), 0);
      const unit = (it.product.base_price + (v?.price_delta || 0) + addOnsDelta);
      return acc + unit * it.quantity;
    }, 0);
    const cfg = config || (await axios.get(`${API_BASE}/config/public`).then(r => r.data));
    const tax_amount = subtotal * (cfg.tax_rate || 0);
    setPricing({ subtotal, discount_amount: 0, tax_amount, tip_amount: tip, total: subtotal + tax_amount + tip });
  };

  useEffect(() => { (async () => { const c = await axios.get(`${API_BASE}/config/public`).then(r => r.data); setConfig(c); })(); }, []);
  useEffect(() => { recalc(); }, [cart, tip]);

  const placeOrder = async () => {
    if (cart.length === 0) return;
    const items = cart.map(it => ({ product_id: it.product_id, variant_id: it.variant_id, quantity: it.quantity, add_on_ids: it.add_on_ids }));
    const payload = {
      items,
      user: { name: form.name, email: form.email, phone: form.phone },
      fulfillment_type: form.fulfillment_type,
      delivery_address: form.fulfillment_type === "delivery" ? { street: form.street, city: form.city, postal_code: form.postal_code } : undefined,
      tip_amount: tip,
    };
    const resp = await axios.post(`${API_BASE}/orders/`, payload);
    const order = resp.data;
    setCart([]);
    navigate(`/order/${order.order_id}`);
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      <div className="max-w-4xl mx-auto px-4 py-10">
        <Link to="/" className="text-sm text-zinc-400">← Back to menu</Link>
        <h1 className="text-3xl font-bold mt-4">Checkout</h1>
        <div className="grid md:grid-cols-2 gap-8 mt-6">
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-zinc-400">Name</label>
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm text-zinc-400">Email</label>
                <input value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2" />
              </div>
              <div>
                <label className="block text-sm text-zinc-400">Phone</label>
                <input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2" />
              </div>
            </div>
            <div>
              <label className="block text-sm text-zinc-400">Fulfillment</label>
              <div className="flex gap-2 mt-1">
                {['pickup', 'delivery'].map(ft => (
                  <button key={ft} onClick={() => setForm({ ...form, fulfillment_type: ft })} className={`px-3 py-1.5 rounded-md text-sm border ${form.fulfillment_type === ft ? 'bg-white text-black border-white' : 'border-zinc-700 text-zinc-300'}`}>{ft}</button>
                ))}
              </div>
            </div>
            {form.fulfillment_type === 'delivery' && (
              <div className="space-y-3">
                <div>
                  <label className="block text-sm text-zinc-400">Street</label>
                  <input value={form.street} onChange={(e) => setForm({ ...form, street: e.target.value })} className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2" />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm text-zinc-400">City</label>
                    <input value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2" />
                  </div>
                  <div>
                    <label className="block text-sm text-zinc-400">Postal Code</label>
                    <input value={form.postal_code} onChange={(e) => setForm({ ...form, postal_code: e.target.value })} className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2" />
                  </div>
                </div>
              </div>
            )}
            <div>
              <label className="block text-sm text-zinc-400">Tip</label>
              <div className="flex gap-2 mt-1">
                {[0, 2, 4, 6].map(t => (
                  <button key={t} onClick={() => setTip(t)} className={`px-3 py-1.5 rounded-md text-sm border ${tip === t ? 'bg-white text-black border-white' : 'border-zinc-700 text-zinc-300'}`}>{t === 0 ? 'No tip' : `$${t}`}</button>
                ))}
              </div>
            </div>
          </div>
          <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4 h-fit">
            <div className="text-sm text-zinc-300">Subtotal <span className="float-right text-white">${pricing.subtotal.toFixed(2)}</span></div>
            <div className="text-sm text-zinc-300 mt-1">Tax <span className="float-right text-white">${pricing.tax_amount.toFixed(2)}</span></div>
            <div className="text-sm text-zinc-300 mt-1">Tip <span className="float-right text-white">${pricing.tip_amount.toFixed(2)}</span></div>
            <div className="text-base font-bold mt-3">Total <span className="float-right">${pricing.total.toFixed(2)}</span></div>
            <button onClick={placeOrder} className="mt-4 w-full px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-black font-semibold">Place Order</button>
            <div className="text-xs text-zinc-400 mt-2">Payment at pickup/delivery (payments coming soon)</div>
          </div>
        </div>
      </div>
    </div>
  );
}

function OrderSuccessPage() {
  const { id } = useParams();
  const [order, setOrder] = useState(null);
  useEffect(() => {
    (async () => {
      if (!id) return;
      try {
        const resp = await axios.get(`${API_BASE}/orders/${id}`);
        setOrder(resp.data);
      } catch (e) {}
    })();
  }, [id]);

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      <div className="max-w-3xl mx-auto px-4 py-16 text-center">
        <h1 className="text-4xl font-black">Thank you!</h1>
        <p className="text-zinc-300 mt-2">Your order has been received and is being prepared.</p>
        <div className="mt-6 bg-zinc-900/60 border border-zinc-800 rounded-xl p-6 text-left">
          <div className="text-sm text-zinc-400">Order ID</div>
          <div className="text-white font-mono">{id}</div>
          <div className="mt-4 text-sm text-zinc-400">Status</div>
          <div className="text-white font-medium">{order?.order_status || 'received'}</div>
          <div className="mt-4 text-sm text-zinc-400">Total</div>
          <div className="text-white font-medium">${order?.totals?.total?.toFixed ? order?.totals?.total?.toFixed(2) : order?.totals?.total}</div>
        </div>
        <Link to="/" className="inline-block mt-8 px-4 py-2 rounded-lg bg-white text-black font-semibold">Back to Menu</Link>
      </div>
    </div>
  );
}

function Shell() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/checkout" element={<CheckoutPage />} />
        <Route path="/order/:id" element={<OrderSuccessPage />} />
      </Routes>
    </BrowserRouter>
  );
}

function App() {
  return <Shell />;
}

export default App;