"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  api,
  ApiError,
  Brand,
  Category,
  money,
  Order,
  Product,
  ProductInput,
  ProductPage,
  Variant,
  VariantInput,
} from "@/lib/api";

type Section = "Dashboard" | "Orders" | "Products" | "Categories" | "Brands";
type Dashboard = {
  awaiting_action: number;
  today_orders: number;
  unavailable_products: number;
  recent_orders: Order[];
};
const sections: Section[] = [
  "Dashboard",
  "Orders",
  "Products",
  "Categories",
  "Brands",
];
const emptyProduct: ProductInput = {
  name: "",
  slug: "",
  brand_id: 0,
  description: "",
  image_url: null,
  active: true,
  available: true,
  category_ids: [],
};
const emptyVariant: VariantInput = {
  name: "",
  mrp: "0.00",
  selling_price: "0.00",
  active: true,
  available: true,
  display_order: 0,
};
function slug(name: string) {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}
function Field({
  label,
  children,
  group = false,
}: {
  label: string;
  children: React.ReactNode;
  group?: boolean;
}) {
  if (group)
    return (
      <fieldset className="field">
        <legend>{label}</legend>
        {children}
      </fieldset>
    );
  return (
    <label className="field">
      <span>{label}</span>
      {children}
    </label>
  );
}
function Flag({
  label,
  value,
  onChange,
}: {
  label: string;
  value: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <label className="flag">
      <input
        type="checkbox"
        checked={value}
        onChange={(e) => onChange(e.target.checked)}
      />
      {label}
    </label>
  );
}
function Badge({ value }: { value: string }) {
  return (
    <span className={`badge ${value.toLowerCase()}`}>
      {value.replaceAll("_", " ")}
    </span>
  );
}
function Modal({
  title,
  close,
  children,
}: {
  title: string;
  close: () => void;
  children: React.ReactNode;
}) {
  const panel = useRef<HTMLElement>(null);
  const closeRef = useRef(close);
  closeRef.current = close;
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const focusable = () =>
      Array.from(
        panel.current?.querySelectorAll<HTMLElement>(
          'button:not(:disabled), input:not(:disabled), select:not(:disabled), textarea:not(:disabled), [tabindex="0"]',
        ) || [],
      );
    focusable()[0]?.focus();
    const handle = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        closeRef.current();
      }
      if (event.key === "Tab") {
        const nodes = focusable();
        const first = nodes[0];
        const last = nodes[nodes.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last?.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first?.focus();
        }
      }
    };
    document.addEventListener("keydown", handle);
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", handle);
      document.body.style.overflow = overflow;
      previous?.focus();
    };
  }, []);
  return (
    <div className="overlay">
      <section
        className="modal"
        ref={panel}
        role="dialog"
        aria-modal="true"
        aria-label={title}
      >
        <header>
          <h2>{title}</h2>
          <button className="quiet" onClick={close}>
            Close
          </button>
        </header>
        {children}
      </section>
    </div>
  );
}
function ImageField({
  value,
  change,
  run,
}: {
  value: string | null | undefined;
  change: (value: string) => void;
  run: (task: () => Promise<void>) => void;
}) {
  return (
    <Field group label="Primary image">
      {value && (
        <img
          className="image-preview"
          src={value}
          alt="Selected catalogue image"
        />
      )}
      <input
        aria-label="Primary image URL"
        value={value || ""}
        placeholder="HTTPS image URL or upload below"
        onChange={(e) => change(e.target.value)}
      />
      <input
        aria-label="Upload image"
        type="file"
        accept="image/jpeg,image/png,image/webp"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file)
            run(async () => {
              const body = new FormData();
              body.set("file", file);
              change(
                (await api<{ image_url: string }>("/images", "POST", body))
                  .image_url,
              );
            });
        }}
      />
      <small>
        JPEG, PNG or WebP · up to 5 MB. Saving replaces the displayed image.
      </small>
    </Field>
  );
}

export default function StoreDesk() {
  const [signedIn, setSignedIn] = useState<boolean | null>(null),
    [section, setSection] = useState<Section>("Dashboard");
  const [busy, setBusy] = useState(false),
    [loading, setLoading] = useState(false),
    [error, setError] = useState(""),
    [notice, setNotice] = useState("");
  const [username, setUsername] = useState(""),
    [password, setPassword] = useState("");
  const [brands, setBrands] = useState<Brand[]>([]),
    [categories, setCategories] = useState<Category[]>([]),
    [products, setProducts] = useState<ProductPage | null>(null),
    [orders, setOrders] = useState<Order[]>([]),
    [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [query, setQuery] = useState(""),
    [search, setSearch] = useState(""),
    [categoryFilter, setCategoryFilter] = useState(""),
    [availability, setAvailability] = useState(""),
    [statusFilter, setStatusFilter] = useState(""),
    [page, setPage] = useState(1),
    [revision, setRevision] = useState(0);
  const [productEdit, setProductEdit] = useState<{
    id?: number;
    data: ProductInput;
    variants: Variant[];
  } | null>(null);
  const [variantEdit, setVariantEdit] = useState<{
    id?: number;
    data: VariantInput;
  } | null>(null);
  const [simpleEdit, setSimpleEdit] = useState<{
    kind: "Brands" | "Categories";
    id?: number;
    name: string;
    slug: string;
    active: boolean;
    image_url: string | null;
    display_order: number;
  } | null>(null);
  const [orderEdit, setOrderEdit] = useState<Order | null>(null),
    [reason, setReason] = useState("");
  const refresh = () => setRevision((n) => n + 1);
  const run = async (task: () => Promise<void>) => {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await task();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
      if (e instanceof ApiError && e.status === 401) setSignedIn(false);
    } finally {
      setBusy(false);
    }
  };
  useEffect(() => {
    api("/me")
      .then(() => setSignedIn(true))
      .catch((e) => {
        setSignedIn(false);
        if (!(e instanceof ApiError && e.status === 401)) setError(e.message);
      });
  }, []);
  useEffect(() => {
    const timer = setTimeout(() => {
      setSearch(query);
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);
  const load = useCallback(
    async (signal: AbortSignal) => {
      const [b, c] = await Promise.all([
        api<Brand[]>("/brands", "GET", undefined, signal),
        api<Category[]>("/categories", "GET", undefined, signal),
      ]);
      if (signal.aborted) return;
      setBrands(b);
      setCategories(c);
      if (section === "Dashboard") {
        const result = await api<Dashboard>(
          "/dashboard",
          "GET",
          undefined,
          signal,
        );
        if (!signal.aborted) setDashboard(result);
      }
      if (section === "Orders") {
        const result = await api<Order[]>(
          `/orders?page=${page}${statusFilter ? "&status=" + statusFilter : ""}`,
          "GET",
          undefined,
          signal,
        );
        if (!signal.aborted) setOrders(result);
      }
      if (section === "Products") {
        const result = await api<ProductPage>(
          `/products?page=${page}&q=${encodeURIComponent(search)}${categoryFilter ? "&category_id=" + categoryFilter : ""}${availability ? "&available=" + availability : ""}`,
          "GET",
          undefined,
          signal,
        );
        if (!signal.aborted) setProducts(result);
      }
    },
    [section, page, search, categoryFilter, availability, statusFilter],
  );
  useEffect(() => {
    if (!signedIn) return;
    let live = true;
    const controller = new AbortController();
    setLoading(true);
    setError("");
    load(controller.signal)
      .catch((e) => {
        if (live) {
          setError(e.message);
          if (e instanceof ApiError && e.status === 401) setSignedIn(false);
        }
      })
      .finally(() => {
        if (live) setLoading(false);
      });
    return () => {
      live = false;
      controller.abort();
    };
  }, [signedIn, load, revision]);
  useEffect(() => {
    if (!signedIn || !["Dashboard", "Orders"].includes(section)) return;
    const timer = setInterval(() => setRevision((n) => n + 1), 30000);
    return () => clearInterval(timer);
  }, [signedIn, section]);
  const choose = (next: Section) => {
    setSection(next);
    setPage(1);
    setError("");
    setNotice("");
  };
  const openProduct = (p: Product) => {
    setProductEdit({
      id: p.id,
      data: {
        name: p.name,
        slug: p.slug,
        description: p.description,
        image_url: p.image_url,
        brand_id: p.brand_id,
        category_ids: p.categories.map((c) => c.id),
        active: p.active,
        available: p.available,
      },
      variants: p.variants,
    });
    setVariantEdit(null);
  };
  const openOrder = (o: Order) => {
    setReason("");
    void run(async () => setOrderEdit(await api<Order>(`/orders/${o.id}`)));
  };
  const orderTable = (rows: Order[]) => (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Order</th>
            <th>Customer</th>
            <th>Fulfilment</th>
            <th>Status</th>
            <th>Payment</th>
            <th>Total</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {rows.map((o) => (
            <tr key={o.id}>
              <td>
                <strong>{o.order_number}</strong>
                <small>{new Date(o.created_at).toLocaleString("en-IN")}</small>
              </td>
              <td>
                {o.customer_phone || "Delivery details removed"}
                {o.customer_deleted_at && (
                  <small>
                    {o.customer_phone
                      ? `Customer deleted · retained until ${new Date(o.delivery_details_erase_at!).toLocaleDateString("en-IN")}`
                      : "Customer deleted · delivery details removed"}
                  </small>
                )}
              </td>
              <td>{o.fulfilment_type}</td>
              <td>
                <Badge value={o.status} />
              </td>
              <td>
                {o.payment_method.replaceAll("_", " ")}
                <small>{o.payment_status}</small>
              </td>
              <td>{money(o.total)}</td>
              <td>
                <button className="quiet" onClick={() => openOrder(o)}>
                  Open
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {!rows.length && <div className="empty">No orders here yet.</div>}
    </div>
  );
  if (signedIn === null)
    return (
      <main className="login">
        <p>Opening your store desk…</p>
      </main>
    );
  if (!signedIn)
    return (
      <main className="login">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void run(async () => {
              await api("/auth/login", "POST", { username, password });
              setPassword("");
              setSignedIn(true);
            });
          }}
        >
          <div className="wordmark">
            goodgrocer<span>STORE DESK</span>
          </div>
          <h1>Welcome back.</h1>
          <p>Sign in to manage your neighbourhood store.</p>
          {error && (
            <div role="alert" className="error">
              {error}
            </div>
          )}
          <Field label="Username">
            <input
              autoComplete="username"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </Field>
          <Field label="Password">
            <input
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </Field>
          <button disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button>
        </form>
      </main>
    );
  return (
    <div className="shell">
      <aside>
        <div className="wordmark">
          goodgrocer<span>STORE DESK</span>
        </div>
        <nav>
          {sections.map((s, i) => (
            <button
              key={s}
              className={section === s ? "selected" : ""}
              onClick={() => choose(s)}
            >
              <span>0{i + 1}</span>
              {s}
            </button>
          ))}
        </nav>
        <div className="aside-bottom">
          <p>
            One store.
            <br />
            Everyday essentials.
          </p>
          <button
            className="quiet"
            onClick={() =>
              void run(async () => {
                await api("/auth/logout", "POST");
                setSignedIn(false);
              })
            }
          >
            Sign out
          </button>
        </div>
      </aside>
      <main className="workspace">
        <header className="page-header">
          <div>
            <p className="eyebrow">YOUR STORE AT A GLANCE</p>
            <h1>{section}</h1>
          </div>
          <button
            className="quiet"
            disabled={busy || loading}
            onClick={refresh}
          >
            Refresh
          </button>
        </header>
        {error && (
          <div className="error" role="alert">
            {error}{" "}
            <button className="quiet" onClick={refresh}>
              Retry
            </button>
          </div>
        )}
        {notice && (
          <div className="success" role="status">
            {notice}
          </div>
        )}
        {loading && (
          <div className="loading" role="status">
            Updating store information…
          </div>
        )}
        {section === "Dashboard" && dashboard && (
          <>
            <div className="stats">
              <article>
                <span>Awaiting action</span>
                <strong>{dashboard.awaiting_action}</strong>
                <button
                  className="quiet"
                  onClick={() => {
                    setStatusFilter("PLACED");
                    choose("Orders");
                  }}
                >
                  Review orders →
                </button>
              </article>
              <article>
                <span>Today’s orders</span>
                <strong>{dashboard.today_orders}</strong>
                <small>Store time · India</small>
              </article>
              <article>
                <span>Unavailable products</span>
                <strong>{dashboard.unavailable_products}</strong>
                <button
                  className="quiet"
                  onClick={() => {
                    setAvailability("false");
                    choose("Products");
                  }}
                >
                  Manage availability →
                </button>
              </article>
            </div>
            <h2>Recent orders</h2>
            {orderTable(dashboard.recent_orders)}
          </>
        )}
        {section === "Orders" && (
          <>
            <div className="toolbar">
              <Field label="Order status">
                <select
                  value={statusFilter}
                  onChange={(e) => {
                    setStatusFilter(e.target.value);
                    setPage(1);
                  }}
                >
                  <option value="">All statuses</option>
                  {[
                    "PLACED",
                    "ACCEPTED",
                    "OUT_FOR_DELIVERY",
                    "DELIVERED",
                    "CANCELLED",
                  ].map((s) => (
                    <option key={s}>{s}</option>
                  ))}
                </select>
              </Field>
              <p>Refreshes every 30 seconds</p>
            </div>
            {orderTable(orders)}
            <div className="pagination">
              <button
                className="quiet"
                disabled={page === 1}
                onClick={() => setPage((n) => n - 1)}
              >
                Previous
              </button>
              <span>Page {page}</span>
              <button
                className="quiet"
                disabled={orders.length < 20}
                onClick={() => setPage((n) => n + 1)}
              >
                Next
              </button>
            </div>
          </>
        )}
        {section === "Products" && (
          <>
            <div className="toolbar">
              <Field label="Search products">
                <input
                  placeholder="Search by name…"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                />
              </Field>
              <Field label="Category">
                <select
                  value={categoryFilter}
                  onChange={(e) => {
                    setCategoryFilter(e.target.value);
                    setPage(1);
                  }}
                >
                  <option value="">All categories</option>
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Availability">
                <select
                  value={availability}
                  onChange={(e) => {
                    setAvailability(e.target.value);
                    setPage(1);
                  }}
                >
                  <option value="">All products</option>
                  <option value="true">Available</option>
                  <option value="false">Unavailable</option>
                </select>
              </Field>
              <button
                onClick={() => {
                  setProductEdit({
                    data: { ...emptyProduct, brand_id: brands[0]?.id || 0 },
                    variants: [],
                  });
                  setVariantEdit(null);
                }}
              >
                + Add product
              </button>
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>Brand</th>
                    <th>Categories</th>
                    <th>Variants</th>
                    <th>Visibility</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {products?.items.map((p) => (
                    <tr key={p.id}>
                      <td>
                        <strong>{p.name}</strong>
                        <small>{p.slug}</small>
                      </td>
                      <td>{p.brand.name}</td>
                      <td>
                        {p.categories.map((c) => c.name).join(", ") || "—"}
                      </td>
                      <td>{p.variants.length}</td>
                      <td>
                        <Badge
                          value={
                            !p.active
                              ? "INACTIVE"
                              : p.available
                                ? "AVAILABLE"
                                : "UNAVAILABLE"
                          }
                        />
                      </td>
                      <td>
                        <button
                          className="quiet"
                          onClick={() => openProduct(p)}
                        >
                          Edit
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {products?.total === 0 && (
                <div className="empty">
                  No products match. Try another search or add a product.
                </div>
              )}
            </div>
            <div className="pagination">
              <button
                className="quiet"
                disabled={page === 1}
                onClick={() => setPage((n) => n - 1)}
              >
                Previous
              </button>
              <span>
                {products?.total || 0} products · Page {page}
              </span>
              <button
                className="quiet"
                disabled={
                  !products || page * products.page_size >= products.total
                }
                onClick={() => setPage((n) => n + 1)}
              >
                Next
              </button>
            </div>
          </>
        )}
        {(section === "Brands" || section === "Categories") && (
          <>
            <div className="toolbar">
              <p>
                {section === "Categories"
                  ? "Flat categories. Products can appear in several."
                  : "Brands available to your catalogue."}
              </p>
              <button
                onClick={() =>
                  setSimpleEdit({
                    kind: section,
                    name: "",
                    slug: "",
                    active: true,
                    image_url: null,
                    display_order: 0,
                  })
                }
              >
                + Add {section === "Brands" ? "brand" : "category"}
              </button>
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Slug</th>
                    {section === "Categories" && <th>Display order</th>}
                    <th>Status</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {(section === "Brands" ? brands : categories).map((row) => (
                    <tr key={row.id}>
                      <td>
                        <strong>{row.name}</strong>
                      </td>
                      <td>{row.slug}</td>
                      {section === "Categories" && (
                        <td>{(row as Category).display_order}</td>
                      )}
                      <td>
                        <Badge value={row.active ? "ACTIVE" : "INACTIVE"} />
                      </td>
                      <td>
                        <button
                          className="quiet"
                          onClick={() =>
                            setSimpleEdit({
                              kind: section,
                              id: row.id,
                              name: row.name,
                              slug: row.slug,
                              active: row.active,
                              image_url: (row as Category).image_url || null,
                              display_order:
                                (row as Category).display_order || 0,
                            })
                          }
                        >
                          Edit
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {!(section === "Brands" ? brands : categories).length && (
                <div className="empty">
                  Add your first {section === "Brands" ? "brand" : "category"}.
                </div>
              )}
            </div>
          </>
        )}
      </main>
      {simpleEdit && (
        <Modal
          title={`${simpleEdit.id ? "Edit" : "Add"} ${simpleEdit.kind === "Brands" ? "brand" : "category"}`}
          close={() => setSimpleEdit(null)}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              void run(async () => {
                const {
                  kind,
                  id,
                  name,
                  slug: handle,
                  active,
                  image_url,
                  display_order,
                } = simpleEdit;
                if (!active && !confirm("Deactivate this record?")) return;
                await api(
                  `/${kind.toLowerCase()}${id ? "/" + id : ""}`,
                  id ? "PUT" : "POST",
                  {
                    name,
                    slug: handle,
                    active,
                    ...(kind === "Categories"
                      ? { image_url, display_order }
                      : {}),
                  },
                );
                setSimpleEdit(null);
                setNotice("Saved successfully.");
                refresh();
              });
            }}
          >
            <fieldset disabled={busy}>
              <Field label="Name">
                <input
                  required
                  value={simpleEdit.name}
                  onChange={(e) =>
                    setSimpleEdit({
                      ...simpleEdit,
                      name: e.target.value,
                      slug: simpleEdit.id
                        ? simpleEdit.slug
                        : slug(e.target.value),
                    })
                  }
                />
              </Field>
              <Field label="Slug">
                <input
                  required
                  pattern="[a-z0-9]+(-[a-z0-9]+)*"
                  value={simpleEdit.slug}
                  onChange={(e) =>
                    setSimpleEdit({ ...simpleEdit, slug: e.target.value })
                  }
                />
              </Field>
              {simpleEdit.kind === "Categories" && (
                <>
                  <Field label="Display order (lower appears first)">
                    <input
                      type="number"
                      value={simpleEdit.display_order}
                      onChange={(e) =>
                        setSimpleEdit({
                          ...simpleEdit,
                          display_order: Number(e.target.value),
                        })
                      }
                    />
                  </Field>
                  <ImageField
                    value={simpleEdit.image_url}
                    change={(image_url) =>
                      setSimpleEdit({ ...simpleEdit, image_url })
                    }
                    run={run}
                  />
                </>
              )}
              <Flag
                label="Active"
                value={simpleEdit.active}
                onChange={(active) => setSimpleEdit({ ...simpleEdit, active })}
              />
              <button>Save</button>
            </fieldset>
          </form>
          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}
        </Modal>
      )}
      {productEdit && (
        <Modal
          title={productEdit.id ? "Edit product" : "Add product"}
          close={() => {
            setProductEdit(null);
            setVariantEdit(null);
          }}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              void run(async () => {
                if (
                  !productEdit.data.active &&
                  !confirm("Hide this product from the catalogue?")
                )
                  return;
                const saved = await api<Product>(
                  `/products${productEdit.id ? "/" + productEdit.id : ""}`,
                  productEdit.id ? "PUT" : "POST",
                  productEdit.data,
                );
                openProduct(saved);
                setNotice("Product saved.");
                refresh();
              });
            }}
          >
            <fieldset disabled={busy}>
              <div className="form-grid">
                <Field label="Product name">
                  <input
                    required
                    maxLength={120}
                    value={productEdit.data.name}
                    onChange={(e) =>
                      setProductEdit({
                        ...productEdit,
                        data: {
                          ...productEdit.data,
                          name: e.target.value,
                          slug: productEdit.id
                            ? productEdit.data.slug
                            : slug(e.target.value),
                        },
                      })
                    }
                  />
                </Field>
                <Field label="Slug">
                  <input
                    required
                    value={productEdit.data.slug}
                    onChange={(e) =>
                      setProductEdit({
                        ...productEdit,
                        data: { ...productEdit.data, slug: e.target.value },
                      })
                    }
                  />
                </Field>
                <Field label="Brand">
                  <select
                    required
                    value={productEdit.data.brand_id || ""}
                    onChange={(e) =>
                      setProductEdit({
                        ...productEdit,
                        data: {
                          ...productEdit.data,
                          brand_id: Number(e.target.value),
                        },
                      })
                    }
                  >
                    <option value="">Choose brand</option>
                    {brands.map((b) => (
                      <option key={b.id} value={b.id}>
                        {b.name}
                        {!b.active ? " (inactive)" : ""}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="Description">
                  <textarea
                    value={productEdit.data.description}
                    onChange={(e) =>
                      setProductEdit({
                        ...productEdit,
                        data: {
                          ...productEdit.data,
                          description: e.target.value,
                        },
                      })
                    }
                  />
                </Field>
              </div>
              <Field group label="Categories">
                <div className="flags">
                  {categories.map((c) => (
                    <Flag
                      key={c.id}
                      label={c.name}
                      value={
                        productEdit.data.category_ids?.includes(c.id) || false
                      }
                      onChange={(checked) =>
                        setProductEdit({
                          ...productEdit,
                          data: {
                            ...productEdit.data,
                            category_ids: checked
                              ? [...(productEdit.data.category_ids || []), c.id]
                              : (productEdit.data.category_ids || []).filter(
                                  (id) => id !== c.id,
                                ),
                          },
                        })
                      }
                    />
                  ))}
                </div>
              </Field>
              <ImageField
                value={productEdit.data.image_url}
                change={(image_url) =>
                  setProductEdit({
                    ...productEdit,
                    data: { ...productEdit.data, image_url },
                  })
                }
                run={run}
              />
              <div className="flags">
                <Flag
                  label="Active in catalogue"
                  value={productEdit.data.active ?? true}
                  onChange={(active) =>
                    setProductEdit({
                      ...productEdit,
                      data: { ...productEdit.data, active },
                    })
                  }
                />
                <Flag
                  label="Available to order"
                  value={productEdit.data.available ?? true}
                  onChange={(available) =>
                    setProductEdit({
                      ...productEdit,
                      data: { ...productEdit.data, available },
                    })
                  }
                />
              </div>
              <button>Save product</button>
            </fieldset>
          </form>
          {productEdit.id && (
            <section className="variants">
              <header>
                <h3>Variants</h3>
                <button
                  className="quiet"
                  onClick={() =>
                    setVariantEdit({
                      data: {
                        ...emptyVariant,
                        display_order: productEdit.variants.length,
                      },
                    })
                  }
                >
                  + Add variant
                </button>
              </header>
              {productEdit.variants.map((v) => (
                <div className="variant-row" key={v.id}>
                  <strong>{v.name}</strong>
                  <span>
                    {money(v.selling_price)} <small>MRP {money(v.mrp)}</small>
                  </span>
                  <Badge
                    value={
                      !v.active
                        ? "INACTIVE"
                        : v.available
                          ? "AVAILABLE"
                          : "UNAVAILABLE"
                    }
                  />
                  <button
                    className="quiet"
                    onClick={() =>
                      setVariantEdit({
                        id: v.id,
                        data: {
                          name: v.name,
                          mrp: v.mrp,
                          selling_price: v.selling_price,
                          active: v.active,
                          available: v.available,
                          display_order: v.display_order,
                        },
                      })
                    }
                  >
                    Edit
                  </button>
                </div>
              ))}
              {!productEdit.variants.length && (
                <p>
                  Add at least one active variant to make this product
                  orderable.
                </p>
              )}
              {variantEdit && (
                <form
                  className="variant-form"
                  onSubmit={(e) => {
                    e.preventDefault();
                    void run(async () => {
                      if (
                        !variantEdit.data.active &&
                        !confirm(
                          "Deactivate this variant? Existing orders keep their history.",
                        )
                      )
                        return;
                      await api(
                        `/products/${productEdit.id}/variants${variantEdit.id ? "/" + variantEdit.id : ""}`,
                        variantEdit.id ? "PUT" : "POST",
                        variantEdit.data,
                      );
                      openProduct(
                        await api<Product>(`/products/${productEdit.id}`),
                      );
                      setNotice("Variant saved.");
                      refresh();
                    });
                  }}
                >
                  <fieldset disabled={busy}>
                    <h3>{variantEdit.id ? "Edit" : "Add"} variant</h3>
                    <div className="form-grid">
                      <Field label="Label">
                        <input
                          required
                          value={variantEdit.data.name}
                          onChange={(e) =>
                            setVariantEdit({
                              ...variantEdit,
                              data: {
                                ...variantEdit.data,
                                name: e.target.value,
                              },
                            })
                          }
                        />
                      </Field>
                      <Field label="MRP (₹)">
                        <input
                          type="number"
                          min="0"
                          step="0.01"
                          required
                          value={variantEdit.data.mrp}
                          onChange={(e) =>
                            setVariantEdit({
                              ...variantEdit,
                              data: {
                                ...variantEdit.data,
                                mrp: e.target.value,
                              },
                            })
                          }
                        />
                      </Field>
                      <Field label="Selling price (₹)">
                        <input
                          type="number"
                          min="0"
                          max={variantEdit.data.mrp}
                          step="0.01"
                          required
                          value={variantEdit.data.selling_price}
                          onChange={(e) =>
                            setVariantEdit({
                              ...variantEdit,
                              data: {
                                ...variantEdit.data,
                                selling_price: e.target.value,
                              },
                            })
                          }
                        />
                      </Field>
                      <Field label="Display order">
                        <input
                          type="number"
                          value={variantEdit.data.display_order}
                          onChange={(e) =>
                            setVariantEdit({
                              ...variantEdit,
                              data: {
                                ...variantEdit.data,
                                display_order: Number(e.target.value),
                              },
                            })
                          }
                        />
                      </Field>
                    </div>
                    <div className="flags">
                      <Flag
                        label="Active"
                        value={variantEdit.data.active ?? true}
                        onChange={(active) =>
                          setVariantEdit({
                            ...variantEdit,
                            data: { ...variantEdit.data, active },
                          })
                        }
                      />
                      <Flag
                        label="Available"
                        value={variantEdit.data.available ?? true}
                        onChange={(available) =>
                          setVariantEdit({
                            ...variantEdit,
                            data: { ...variantEdit.data, available },
                          })
                        }
                      />
                    </div>
                    <button>Save variant</button>
                    <button
                      type="button"
                      className="quiet"
                      onClick={() => setVariantEdit(null)}
                    >
                      Cancel
                    </button>
                  </fieldset>
                </form>
              )}
            </section>
          )}
          {error && (
            <p role="alert" className="error">
              {error}
            </p>
          )}
          {notice && (
            <p role="status" className="success">
              {notice}
            </p>
          )}
        </Modal>
      )}
      {orderEdit && (
        <Modal title={orderEdit.order_number} close={() => setOrderEdit(null)}>
          <div className="order-summary">
            <Badge value={orderEdit.status} />
            <p>
              {orderEdit.customer_phone || "Delivery details removed"} ·{" "}
              {orderEdit.fulfilment_type}
            </p>
            {orderEdit.customer_deleted_at && (
              <p className="error">
                {orderEdit.customer_phone
                  ? `Customer deleted. Delivery details retained until ${new Date(orderEdit.delivery_details_erase_at!).toLocaleDateString("en-IN")}.`
                  : "Customer deleted. Delivery details removed."}
              </p>
            )}
            <p>
              {orderEdit.payment_method.replaceAll("_", " ")} ·{" "}
              <strong>{orderEdit.payment_status}</strong>
            </p>
            {orderEdit.address_snapshot && (
              <address>
                {Object.entries(orderEdit.address_snapshot)
                  .filter(
                    ([k, v]) => v && !["latitude", "longitude"].includes(k),
                  )
                  .map(([k, v]) => (
                    <span key={k}>
                      {String(v)}
                      <br />
                    </span>
                  ))}
              </address>
            )}
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Item</th>
                  <th>Qty</th>
                  <th>Price</th>
                  <th>Total</th>
                </tr>
              </thead>
              <tbody>
                {orderEdit.items.map((i) => (
                  <tr key={i.variant_id}>
                    <td>
                      {i.product_name}
                      <small>{i.variant_name}</small>
                    </td>
                    <td>{i.quantity}</td>
                    <td>{money(i.unit_selling_price)}</td>
                    <td>{money(i.line_total)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="totals">
            <p>
              Subtotal <strong>{money(orderEdit.subtotal)}</strong>
            </p>
            <p>
              Delivery <strong>{money(orderEdit.delivery_fee)}</strong>
            </p>
            <p>
              Total <strong>{money(orderEdit.total)}</strong>
            </p>
          </div>
          {orderEdit.cancellation_reason && (
            <p className="error">Cancelled: {orderEdit.cancellation_reason}</p>
          )}
          <div className="actions">
            {(orderEdit.status === "PLACED"
              ? ["ACCEPTED"]
              : orderEdit.status === "ACCEPTED"
                ? [
                    orderEdit.fulfilment_type === "PICKUP"
                      ? "DELIVERED"
                      : "OUT_FOR_DELIVERY",
                  ]
                : orderEdit.status === "OUT_FOR_DELIVERY"
                  ? ["DELIVERED"]
                  : []
            ).map((status) => (
              <button
                disabled={busy}
                key={status}
                onClick={() =>
                  void run(async () => {
                    setOrderEdit(
                      await api<Order>(
                        `/orders/${orderEdit.id}/status`,
                        "POST",
                        { status },
                      ),
                    );
                    refresh();
                    setNotice("Order updated.");
                  })
                }
              >
                {status === "ACCEPTED"
                  ? "Accept order"
                  : status === "DELIVERED"
                    ? "Mark delivered / collected"
                    : "Out for delivery"}
              </button>
            ))}
            {orderEdit.payment_method !== "ONLINE_UPI" &&
              orderEdit.payment_status === "PENDING" &&
              orderEdit.status !== "CANCELLED" && (
                <button
                  className="quiet"
                  disabled={busy}
                  onClick={() =>
                    void run(async () => {
                      if (confirm("Confirm that payment has been received?")) {
                        setOrderEdit(
                          await api<Order>(
                            `/orders/${orderEdit.id}/mark-paid`,
                            "POST",
                          ),
                        );
                        refresh();
                      }
                    })
                  }
                >
                  Payment received
                </button>
              )}
          </div>
          {!["DELIVERED", "CANCELLED"].includes(orderEdit.status) && (
            <div className="cancel">
              <Field label="Cancellation reason">
                <input
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="For example, address outside delivery area"
                />
              </Field>
              <button
                className="danger"
                disabled={busy || !reason.trim()}
                onClick={() =>
                  void run(async () => {
                    if (confirm("Cancel this order? This cannot be undone.")) {
                      setOrderEdit(
                        await api<Order>(
                          `/orders/${orderEdit.id}/status`,
                          "POST",
                          { status: "CANCELLED", reason },
                        ),
                      );
                      refresh();
                    }
                  })
                }
              >
                Cancel order
              </button>
            </div>
          )}
          {error && (
            <p role="alert" className="error">
              {error}
            </p>
          )}
        </Modal>
      )}
    </div>
  );
}
