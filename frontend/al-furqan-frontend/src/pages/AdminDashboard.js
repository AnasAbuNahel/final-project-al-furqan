import React, { useState, useEffect } from "react";
import { toast, Toaster } from "react-hot-toast";

const AdminDashboard = () => {
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState({ username: "", password: "", tenant: "" });
  const authToken = localStorage.getItem("token");
  const userRole = localStorage.getItem("role");

  const addNotification = (msg, success = true) => {
    const style = {
      borderRadius: "10px",
      fontWeight: "bold",
      padding: "14px",
      fontFamily: "Tahoma",
      direction: "rtl",
    };
    if (success) {
      toast.success(msg, {
        icon: "✅",
        style: { ...style, background: "#e6fffa", color: "#00796b" },
      });
    } else {
      toast.error(msg, {
        icon: "❌",
        style: { ...style, background: "#ffe6e6", color: "#c62828" },
      });
    }
  };

  const fetchWithAuth = (url, options = {}) => {
    if (!authToken) {
      addNotification("يرجى تسجيل الدخول أولاً", false);
      return Promise.reject(new Error("No auth token"));
    }
    const headers = {
      Authorization: `Bearer ${authToken}`,
      "Content-Type": "application/json",
      ...(options.headers || {}),
    };
    return fetch(url, { ...options, headers });
  };

  const loadUsers = () => {
    fetchWithAuth("https://final-project-al-furqan-2389.onrender.com/api/users")
      .then(async (res) => {
        const json = await res.json();
        if (!res.ok) throw new Error(json.error || "فشل في تحميل قائمة المستخدمين");
        return json;
      })
      .then(setUsers)
      .catch((err) => addNotification(err.message, false));
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const handleAddUser = () => {
    if (!form.username || !form.password || !form.tenant) {
      return addNotification("⚠️ يرجى إدخال جميع البيانات المطلوبة", false);
    }

    fetchWithAuth("https://final-project-al-furqan-2389.onrender.com/api/users/create", {
      method: "POST",
      body: JSON.stringify({ ...form, role: "admin" }),
    })
      .then(async (res) => {
        const json = await res.json();
        if (!res.ok) throw new Error(json.error || "حدث خطأ أثناء إنشاء المستخدم");
        return json;
      })
      .then((newUser) => {
        addNotification(`✅ تم إنشاء مدير جديد بنجاح للجهة: ${newUser.tenant}`);
        loadUsers();
        setForm({ username: "", password: "", tenant: "" });
      })
      .catch((err) => addNotification(err.message, false));
  };

  const handleDeleteUser = (id, username) => {
    console.log("Auth Token:", authToken);
    if (!window.confirm(`هل تريد بالتأكيد حذف المستخدم "${username}" ؟`)) return;

    fetchWithAuth(`https://final-project-al-furqan-2389.onrender.com/api/users/dashboard/${id}`, { method: "DELETE" })
      .then(async (res) => {
        const json = await res.json();
        if (!res.ok) throw new Error(json.error || "فشل في حذف المستخدم");
        return json;
      })
      .then(() => {
        addNotification(`🗑️ تم حذف المستخدم "${username}" بنجاح`);
        setUsers((prev) => prev.filter((u) => u.id !== id));
      })
      .catch((err) => addNotification(err.message, false));
  };

  return (
    <div style={styles.container}>
      <Toaster position="top-center" reverseOrder={false} />
      <h2 style={styles.header}>📋 إدارة المستخدمين</h2>

      <div style={styles.card}>
        <h3 style={styles.cardTitle}>➕ إنشاء مدير جديد</h3>
        <input
          type="text"
          placeholder="اسم المستخدم"
          value={form.username}
          onChange={(e) => setForm({ ...form, username: e.target.value })}
          style={styles.input}
        />
        <input
          type="password"
          placeholder="كلمة المرور"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          style={styles.input}
        />
        <input
          type="text"
          placeholder="اسم الجهة"
          value={form.tenant}
          onChange={(e) => setForm({ ...form, tenant: e.target.value })}
          style={styles.input}
        />
        <button onClick={handleAddUser} style={styles.button}>
          إنشاء
        </button>
      </div>

      {users.length > 0 ? (
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>👥 قائمة المدراء الحاليين</h3>
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>#</th>
                <th style={styles.th}>اسم المستخدم</th>
                <th style={styles.th}>الجهة</th>
                <th style={styles.th}>الدور</th>
                <th style={styles.th}>إجراء</th>
              </tr>
            </thead>
            <tbody>
            {users
              .filter((u) => u.role !== "user")   
              .map((u, index) => (
                <tr key={u.id} style={styles.tr}>
                  <td style={styles.td}>{index + 1}</td>
                  <td style={styles.td}>{u.username}</td>
                  <td style={styles.td}>{u.tenant || "-"}</td>
                  <td style={styles.td}>{u.role || "-"}</td>
                  <td style={styles.td}>
                    <button
                      onClick={() => handleDeleteUser(u.id, u.username)}
                      style={{ ...styles.button, backgroundColor: "#dc3545" }}
                    >
                      حذف
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p style={{ textAlign: "center", color: "#777" }}>⚠️ لا يوجد مدراء مضافين حتى الآن</p>
      )}
    </div>
  );
};

const styles = {
  container: {
    padding: "60px 20px 40px",
    fontFamily: "Tahoma, sans-serif",
    direction: "rtl",
    maxWidth: "800px",
    margin: "0 auto",
  },
  header: {
    fontSize: "30px",
    fontWeight: "bold",
    marginBottom: "30px",
    color: "#003366",
    textAlign: "center",
  },
  card: {
    backgroundColor: "#fff",
    borderRadius: "14px",
    padding: "25px",
    marginBottom: "25px",
    boxShadow: "0 6px 14px rgba(0,0,0,0.12)",
    transition: "0.3s",
  },
  cardTitle: {
    fontSize: "20px",
    fontWeight: "600",
    marginBottom: "20px",
    color: "#004085",
    textAlign: "center",
  },
  input: {
    width: "100%",
    padding: "12px",
    marginBottom: "15px",
    borderRadius: "8px",
    border: "1px solid #ccc",
    fontSize: "15px",
    boxSizing: "border-box",
  },
  button: {
    backgroundColor: "#007bff",
    color: "white",
    padding: "12px",
    borderRadius: "8px",
    border: "none",
    fontSize: "16px",
    cursor: "pointer",
    fontWeight: "bold",
    width: "100%",
    transition: "background-color 0.3s ease",
  },
  table: {
    width: "100%",
    borderCollapse: "collapse",
  },
  th: {
    borderBottom: "2px solid #ccc",
    padding: "12px",
    textAlign: "center",
    fontWeight: "600",
    backgroundColor: "#f8f9fa",
    color: "#004085",
  },
  td: {
    borderBottom: "1px solid #eee",
    padding: "10px",
    textAlign: "center",
  },
  tr: {
    transition: "background 0.2s",
  },
};

export default AdminDashboard;


