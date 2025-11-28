import React, { useState, useEffect, useMemo } from "react";
import { FaArrowDown, FaArrowUp, FaDollarSign, FaBoxOpen, FaDonate } from "react-icons/fa";
import { useNavigate } from "react-router-dom";
import toast, { Toaster } from "react-hot-toast";
import axios from "axios";
import * as XLSX from "xlsx";
import { saveAs } from "file-saver";
import CountUp from "react-countup";
import { motion } from "framer-motion";

// إعداد Axios
axios.defaults.baseURL = "https://final-project-al-furqan-rj1r.onrender.com";
axios.defaults.headers.common["Authorization"] = `Bearer ${localStorage.getItem("token")}`;

// Utilities
const toNumber = (v) => {
  const n = parseFloat(v);
  return Number.isFinite(n) ? n : 0;
};
const sumBy = (arr, fn) => arr.reduce((s, x) => s + toNumber(fn(x)), 0);
const groupBySum = (arr, keyFn, valFn) => {
  const map = {};
  for (const item of arr) {
    const k = keyFn(item);
    map[k] = (map[k] || 0) + toNumber(valFn(item));
  }
  return Object.entries(map)
    .map(([label, value]) => ({ label, value }))
    .sort((a, b) => b.value - a.value);
};
const formatCurrency = (n) => `${toNumber(n).toLocaleString("ar-EG")} شيكل`;

const formatParcelCount = (n) => `${toNumber(n).toLocaleString("ar-EG")} طرد`;

const Dashboard = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);

  const [imports, setImports] = useState([]);
  const [exports, setExports] = useState([]);

  const [importData, setImportData] = useState({
    source: "",
    name: "",
    date: "",
    type: "",
    amount: "",
  });

  const [exportData, setExportData] = useState({
    description: "",
    amount: "",
    date: "",
  });

  const navigate = useNavigate();

  // إجماليات
  const totalImports = useMemo(
    () => imports.filter((imp) => imp.type === "مساعدات نقدية").reduce((sum, imp) => sum + toNumber(imp.amount), 0),
    [imports]
  );
  const totalExports = useMemo(() => exports.reduce((sum, exp) => sum + toNumber(exp.amount), 0), [exports]);
  const totalBalance = totalImports - totalExports;

  // واردات الطرود
  const parcels = useMemo(() => imports.filter((imp) => (imp.type || "").includes("طرود")), [imports]);
  const parcelTotals = useMemo(() => groupBySum(parcels, (x) => x.type || "غير محدد", (x) => x.amount), [parcels]);
  const parcelsGrandTotal = useMemo(() => sumBy(parcelTotals, (x) => x.value), [parcelTotals]);

  // واردات المساعدات النقدية فقط
  const cashImports = useMemo(
    () => imports.filter((imp) => imp.type === "مساعدات نقدية"),
    [imports]
  );

  const sourceTotals = useMemo(
    () => groupBySum(cashImports, (x) => x.source || "غير محدد", (x) => x.amount),
    [cashImports]
  );

  const sourcesGrandTotal = useMemo(
    () => sumBy(sourceTotals, (x) => x.value),
    [sourceTotals]
  );


  // الصادرات حسب الفئة
  const exportTotals = useMemo(() => groupBySum(exports, (x) => x.description || "غير محدد", (x) => x.amount), [exports]);
  const exportGrandTotal = useMemo(() => sumBy(exportTotals, (x) => x.value), [exportTotals]);

  // الطباعة والتصدير
  const handlePrint = () => {
    const printSection = document.querySelector(".print-section");
    if (!printSection) return;
    printSection.style.display = "block";
    setTimeout(() => {
      window.print();
      printSection.style.display = "none";
    }, 300);
  };

  const handleExportExcel = () => {
    const data = [["م", "الواردات - البيان", "الواردات - المبلغ", "الصادرات - التاريخ", "الصادرات - البيان", "الصادرات - المبلغ"]];
    const maxRows = Math.max(imports.length, exports.length);
    for (let i = 0; i < maxRows; i++) {
      data.push([
        i + 1,
        `${imports[i]?.name || ""} - ${imports[i]?.source || ""}`,
        imports[i]?.amount || "",
        exports[i]?.date || "",
        exports[i]?.description || "",
        exports[i]?.amount || "",
      ]);
    }
    data.push([]);
    data.push(["", "إجمالي الواردات (نقدية)", totalImports, "", "إجمالي الصادرات", totalExports]);
    data.push(["", "", "", "", "الرصيد", totalBalance]);
    const ws = XLSX.utils.aoa_to_sheet(data);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "التقرير المالي");
    const excelBuffer = XLSX.write(wb, { bookType: "xlsx", type: "array" });
    const blob = new Blob([excelBuffer], { type: "application/octet-stream" });
    saveAs(blob, "التقرير_المالي.xlsx");
  };

  // فتح/إغلاق النوافذ
  const openModal = () => setIsModalOpen(true);
  const closeModal = () => setIsModalOpen(false);
  const openExportModal = () => setIsExportModalOpen(true);
  const closeExportModal = () => setIsExportModalOpen(false);

  // الحفظ
  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.post("https://final-project-al-furqan-rj1r.onrender.com/api/imports", importData);
      setImports((prev) => [...prev, res.data]);
      toast.success("تم حفظ الإيراد بنجاح");
      closeModal();
      setImportData({ source: "", name: "", date: "", type: "", amount: "" });
    } catch (error) {
      toast.error("حدث خطأ أثناء حفظ الإيراد");
    }
  };

  const handleExportSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.post("https://final-project-al-furqan-rj1r.onrender.com/api/exports", exportData);
      setExports((prev) => [...prev, res.data]);
      toast.success("تم حفظ الصادر بنجاح");
      closeExportModal();
      setExportData({ description: "", amount: "", date: "" });
    } catch (error) {
      toast.error("حدث خطأ أثناء حفظ الصادر");
    }
  };

  // جلب البيانات
  useEffect(() => {
    const fetchData = async () => {
      const token = localStorage.getItem("token");
      if (!token) {
        toast.error("انتهت صلاحية الجلسة");
        navigate("/login");
        return;
      }
      try {
        const [importRes, exportRes] = await Promise.all([
          axios.get("/api/imports", { headers: { Authorization: `Bearer ${token}` } }),
          axios.get("/api/exports", { headers: { Authorization: `Bearer ${token}` } }),
        ]);
        setImports(importRes.data || []);
        setExports(exportRes.data || []);
      } catch {
        toast.error("فشل في تحميل البيانات");
      }
    };
    fetchData();
  }, [navigate]);

  return (
    <div style={styles.page} dir="rtl">
      <Toaster position="top-center" />
      <h1 style={styles.pageTitle}>الصفحة الرئيسية</h1>

      {/* البطاقات */}
      <div style={styles.cardGroup}>
        <StatCard title="إجمالي الواردات (نقدية)" icon={<FaArrowDown size={28} />} value={totalImports} gradient="linear-gradient(135deg, #3BA5EA, #1f78d1)" />
        <StatCard title="إجمالي الصادرات" icon={<FaArrowUp size={28} />} value={totalExports} gradient="linear-gradient(135deg, #34d399, #10b981)" />
        <StatCard title="إجمالي الرصيد" icon={<FaDollarSign size={28} />} value={totalBalance} gradient="linear-gradient(135deg, #a78bfa, #8b5cf6)" />
      </div>

      {/* الأزرار */}
      <div style={styles.buttonGroup}>
        <MotionButton onClick={openModal} label="تسجيل الواردات" gradient="#1f78d1" />
        <MotionButton onClick={openExportModal} label="تسجيل الصادرات" gradient="#10b981" />
        <MotionButton onClick={handlePrint} label="طباعة التقرير المالي" gradient="#334155" />
        <MotionButton onClick={handleExportExcel} label="تصدير كـ Excel" gradient="#334155" />
      </div>

      {/* الأقسام */}
      <div style={styles.sectionsGrid}>
        <SectionCard title="واردات المساعدات النقدية" icon={<FaDonate />}>
          {sourceTotals.length === 0 ? <EmptyHint text="لا توجد بيانات واردات بعد" /> :
            sourceTotals.map((row, idx) => (
              <ProgressRow key={idx} label={row.label} value={row.value} total={Math.max(1, sourcesGrandTotal)} color={palette[idx % palette.length]} />
            ))}
          <Divider />
          <RowSummary label="إجمالي الواردات" value={formatCurrency(sourcesGrandTotal)} />
        </SectionCard>

        <SectionCard title="واردات الطرود حسب النوع" icon={<FaBoxOpen />}>
          {parcelTotals.length === 0 ? <EmptyHint text="لا توجد واردات طرود بعد" /> :
            parcelTotals.map((row, idx) => (
              <ProgressRow key={idx} label={row.label} value={row.value} total={Math.max(1, parcelsGrandTotal)} color={parcelPalette[idx % parcelPalette.length]} />
            ))}
          <Divider />
          <RowSummary label="إجمالي واردات الطرود" value={formatParcelCount(parcelsGrandTotal)} />
        </SectionCard>

        <SectionCard title="توزيع الصادرات حسب الفئة" icon={<FaArrowUp />}>
          {exportTotals.length === 0 ? <EmptyHint text="لا توجد بيانات صادرات بعد" /> :
            exportTotals.map((row, idx) => (
              <ProgressRow key={idx} label={row.label} value={row.value} total={Math.max(1, exportGrandTotal)} color={exportPalette[idx % exportPalette.length]} />
            ))}
          <Divider />
          <RowSummary label="إجمالي الصادرات" value={formatCurrency(exportGrandTotal)} />
        </SectionCard>
      </div>

      {/* نافذة تسجيل وارد */}
      {isModalOpen && (
        <div style={modalStyles.overlay}>
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            style={modalStyles.modal}
          >
            <h2 style={modalStyles.title}>تسجيل وارد جديد</h2>
            <form onSubmit={handleSubmit}>
              
              {/* الجهة الموردة */}
              <div style={{ marginBottom: 12 }}>
                <label>الجهة الموردة</label>
                <select
                  value={importData.source}
                  onChange={(e) => setImportData({ ...importData, source: e.target.value })}
                  style={modalStyles.input}
                  required
                >
                  <option value="">اختر الجهة</option>
                  <option value="مبادرين">مبادرين</option>
                  <option value="طوارئ">طوارئ</option>
                  <option value="مؤسسات خيرية">مؤسسات خيرية</option>
                </select>
              </div>

              {/* اسم المورد */}
              <div style={{ marginBottom: 12 }}>
                <label>اسم المورد</label>
                <input
                  type="text"
                  value={importData.name}
                  onChange={(e) => setImportData({ ...importData, name: e.target.value })}
                  style={modalStyles.input}
                  required
                />
              </div>

              {/* تاريخ الإيراد */}
              <div style={{ marginBottom: 12 }}>
                <label>تاريخ الإيراد</label>
                <input
                  type="date"
                  value={importData.date}
                  onChange={(e) => setImportData({ ...importData, date: e.target.value })}
                  style={modalStyles.input}
                  required
                />
              </div>

              {/* نوع الإيراد */}
              <div style={{ marginBottom: 12 }}>
                <label>نوع الإيراد</label>
                <select
                  value={importData.type}
                  onChange={(e) => setImportData({ ...importData, type: e.target.value })}
                  style={modalStyles.input}
                  required
                >
                  <option value="">اختر النوع</option>
                  <option value="طرود غذائية">طرود غذائية</option>
                  <option value="طرود خضرة">طرود خضرة</option>
                  <option value="طرود صحية">طرود صحية</option>
                  <option value="مساعدات نقدية">مساعدات نقدية</option>
                  <option value="غير ذلك">غير ذلك</option>
                </select>
              </div>

              {/* يظهر فقط إذا كان نوع الإيراد "مساعدات نقدية" */}
              {importData.type === "مساعدات نقدية" && (
                <div style={{ marginBottom: 12 }}>
                  <label>المبلغ</label>
                  <input
                    type="number"
                    value={importData.amount}
                    onChange={(e) => setImportData({ ...importData, amount: e.target.value })}
                    style={modalStyles.input}
                    required
                  />
                </div>
              )}

              {/* يظهر فقط إذا كان نوع الإيراد "غير ذلك" */}
              {importData.type === "غير ذلك" && (
                <div style={{ marginBottom: 12 }}>
                  <label>حدد نوع الإيراد</label>
                  <input
                    type="text"
                    value={importData.otherType || ""}
                    onChange={(e) => setImportData({ ...importData, otherType: e.target.value })}
                    style={modalStyles.input}
                    required
                  />
                </div>
              )}
              {/* عدد الطرود يظهر فقط إذا كان النوع طرود */}
              {importData.type.includes("طرود") && (
                <div style={{ marginBottom: 12 }}>
                  <label>عدد الطرود</label>
                  <input
                    type="number"
                    value={importData.amount}
                    onChange={(e) => setImportData({ ...importData, amount: e.target.value })}
                    style={modalStyles.input}
                    required
                  />
                </div>
              )}

              <div style={modalStyles.actions}>
                <MotionButton label="إلغاء" onClick={closeModal} gradient="#ef4444" />
                <MotionButton label="حفظ" gradient="#10b981" />
              </div>
            </form>
          </motion.div>
        </div>
      )}


      {/* نافذة تسجيل صادر */}
      {isExportModalOpen && (
        <div style={modalStyles.overlay}>
          <motion.div initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} style={modalStyles.modal}>
            <h2 style={modalStyles.title}>تسجيل صادر جديد</h2>
            <form onSubmit={handleExportSubmit}>
              {[
                { label: "البيان", key: "description", type: "text" },
                { label: "المبلغ", key: "amount", type: "number" },
                { label: "التاريخ", key: "date", type: "date" },
              ].map((f, idx) => (
                <div key={idx} style={{ marginBottom: 12 }}>
                  <label>{f.label}</label>
                  <input type={f.type} value={exportData[f.key]} onChange={(e) => setExportData({ ...exportData, [f.key]: e.target.value })} style={modalStyles.input} required />
                </div>
              ))}
              <div style={modalStyles.actions}>
                <MotionButton label="إلغاء" onClick={closeExportModal} gradient="#ef4444" />
                <MotionButton label="حفظ" gradient="#10b981" />
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </div>
  );
};

/** Components */
const StatCard = ({ icon, title, value, gradient }) => (
  <motion.div whileHover={{ scale: 1.04, translateY: -4 }} transition={{ type: "spring", stiffness: 260, damping: 18 }} style={{ background: gradient, padding: 20, borderRadius: 16, color: "white", minWidth: 260, textAlign: "center", boxShadow: "0 10px 25px rgba(0,0,0,0.15)" }}>
    <div>{icon}</div>
    <h4 style={{ margin: "12px 0 6px", fontWeight: 800 }}>{title}</h4>
    <p style={{ fontSize: 24, fontWeight: 900, margin: 0 }}>
      <CountUp end={toNumber(value)} duration={1.2} separator="," /> <span style={{ fontSize: 16 }}>شيكل</span>
    </p>
  </motion.div>
);

const MotionButton = ({ label, onClick, gradient }) => (
  <motion.button whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.98 }} onClick={onClick} style={{ background: gradient, color: "#fff", padding: "10px 18px", border: "none", borderRadius: 10, cursor: "pointer", fontWeight: 700, margin: "0 5px" }}>
    {label}
  </motion.button>
);

const SectionCard = ({ title, icon, children }) => (
  <div style={{ background: "#fff", borderRadius: 16, padding: 20, boxShadow: "0 8px 24px rgba(0,0,0,0.06)", border: "1px solid #eef2f7" }}>
    <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
      <div style={{ color: "#334155" }}>{icon}</div>
      <h3 style={{ margin: 0, color: "#0f172a", fontSize: 18, fontWeight: 800 }}>{title}</h3>
    </div>
    {children}
  </div>
);

const ProgressRow = ({ label, value, total, color }) => {
  const percent = Math.max(0, Math.min(100, (toNumber(value) / Math.max(1, toNumber(total))) * 100));
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
        <strong>{label}</strong>
        <span>{percent.toFixed(1)}%</span>
      </div>
      <div style={{ background: "#f1f5f9", borderRadius: 999, overflow: "hidden", height: 14 }}>
        <motion.div initial={{ width: 0 }} animate={{ width: `${percent}%` }} transition={{ duration: 0.9 }} style={{ height: "100%", background: color }} />
      </div>
    </div>
  );
};

const Divider = () => <div style={{ height: 1, background: "#e2e8f0", margin: "12px 0" }} />;
const RowSummary = ({ label, value }) => (<div style={{ display: "flex", justifyContent: "space-between", fontWeight: 800 }}><span>{label}</span><span>{value}</span></div>);
const EmptyHint = ({ text }) => (<div style={{ padding: 12, borderRadius: 10, background: "#f8fafc", color: "#475569" }}>{text}</div>);

// ستايل النوافذ
const modalStyles = {
  overlay: { position: "fixed", top: 0, left: 0, width: "100%", height: "100%", background: "rgba(0,0,0,0.5)", display: "flex", justifyContent: "center", alignItems: "center", zIndex: 1000 },
  modal: { background: "#fff", borderRadius: 12, padding: 20, width: "90%", maxWidth: 400, boxShadow: "0 10px 30px rgba(0,0,0,0.2)" },
  title: { marginBottom: 16, fontSize: 20, fontWeight: 800 },
  input: { width: "100%", padding: "8px 12px", borderRadius: 6, border: "1px solid #ddd", marginTop: 4 },
  actions: { display: "flex", justifyContent: "flex-end", marginTop: 16, gap: 10 },
};

const styles = {
  page: { minHeight: "100vh", background: "linear-gradient(180deg, #f0f4f8, #eef2f7)", padding: 30 },
  pageTitle: { textAlign: "center", fontSize: 28, fontWeight: 900, marginBottom: 24 },
  cardGroup: { display: "flex", flexWrap: "wrap", justifyContent: "center", gap: 18, marginBottom: 22 },
  buttonGroup: { display: "flex", justifyContent: "center", flexWrap: "wrap", gap: 14, marginBottom: 22 },
  sectionsGrid: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 18, marginTop: 10 },
};

const palette = ["#3BA5EA", "#10B981", "#8B5CF6", "#F59E0B", "#EF4444"];
const parcelPalette = ["#F59E0B", "#F97316", "#10B981", "#06B6D4", "#8B5CF6"];
const exportPalette = ["#10B981", "#06B6D4", "#3BA5EA", "#8B5CF6", "#F43F5E"];

export default Dashboard;
