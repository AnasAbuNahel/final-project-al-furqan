import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const AddResident = () => {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    husband_name: '',
    husband_id_number: '',
    wife_name: '',
    wife_id_number: '',
    phone_number: '',
    num_family_members: '',
    injuries: '',
    diseases: '',
    damage_level: '',
    neighborhood: '',
    notes: '',
    residence_status: '', // 👈 جديد
  });

  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const validatePhone = (phone_number) => {
    return /^05[69]\d{7}$/.test(phone_number);
  };

  const checkIfResidentExists = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('https://final-project-al-furqan-rj1r.onrender.com/api/residents/check', {
        params: {
          husband_id_number: formData.husband_id_number,
          wife_id_number: formData.wife_id_number,
          phone_number: formData.phone_number
        },
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      return response.data.exists;
    } catch (error) {
      console.error('Error checking resident:', error);
      return false;
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (formData.num_family_members < 1) {
      toast.error('❌ عدد أفراد الأسرة يجب أن يكون 1 أو أكثر');
      return;
    }

    if (formData.husband_id_number.length < 9 || formData.wife_id_number.length < 9) {
      toast.error('❌ رقم الهوية يجب أن يكون 9 أرقام على الأقل');
      return;
    }

    if (!validatePhone(formData.phone_number)) {
      toast.error('❌ رقم الجوال غير صحيح. يجب أن يبدأ بـ059 أو 056 ويتكون من 10 أرقام');
      return;
    }

    if (!formData.residence_status) {
      toast.error('❌ يرجى اختيار حالة الإقامة');
      return;
    }

    setLoading(true);

    const residentExists = await checkIfResidentExists();
    if (residentExists) {
      toast.error('❌ المستفيد موجود مسبقًا في النظام');
      setLoading(false);
      return;
    }

    try {
      const token = localStorage.getItem('token');
      await axios.post('https://final-project-al-furqan-rj1r.onrender.com/api/residents', formData, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      toast.success(`✅ تم إضافة المستفيد ${formData.husband_name} بنجاح`);
      setTimeout(() => {
        navigate('/residents');
      }, 2000);
    } catch (error) {
      toast.error(`❌ حدث خطأ: ${error.response?.data?.error || 'يرجى المحاولة لاحقًا'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    navigate('/residents');
  };

  return (
    <div style={styles.container}>
      <ToastContainer position="top-center" autoClose={3000} />
      <style>{responsiveStyle}</style>
      <h2>إضافة مستفيد جديد</h2>
      <form onSubmit={handleSubmit} style={styles.form}>
        <input type="text" name="husband_name" placeholder="اسم الزوج" value={formData.husband_name} onChange={handleChange} required style={styles.input} />
        <input type="number" name="husband_id_number" placeholder="رقم هوية الزوج" value={formData.husband_id_number} onChange={handleChange} required style={styles.input} />
        <input type="text" name="wife_name" placeholder="اسم الزوجة" value={formData.wife_name} onChange={handleChange} required style={styles.input} />
        <input type="number" name="wife_id_number" placeholder="رقم هوية الزوجة" value={formData.wife_id_number} onChange={handleChange} required style={styles.input} />
        <input type="number" name="phone_number" placeholder="رقم الجوال" value={formData.phone_number} onChange={handleChange} required style={styles.input} />
        <input type="number" name="num_family_members" placeholder="عدد أفراد الأسرة" value={formData.num_family_members} onChange={handleChange} required style={styles.input} />
        <input type="text" name="injuries" placeholder="الإصابات إن وجدت" value={formData.injuries} onChange={handleChange} style={styles.input} />
        <input type="text" name="diseases" placeholder="الأمراض إن وجدت" value={formData.diseases} onChange={handleChange} style={styles.input} />

        {/* 👇 حقل جديد لحالة الإقامة */}
        <select name="residence_status" value={formData.residence_status} onChange={handleChange} required style={styles.input}>
          <option value="">اختر حالة الإقامة</option>
          <option value="مقيم">مقيم</option>
          <option value="نازح">نازح</option>
        </select>

        <select name="damage_level" value={formData.damage_level} onChange={handleChange} required style={styles.input}>
          <option value="">اختر نوع الضرر</option>
          <option value="كلي">كلي</option>
          <option value="جزئي بليغ">جزئي بليغ</option>
          <option value="جزئي">طفيف</option>
          <option value="لا يوجد ضرر">لا يوجد ضرر</option>
        </select>

        <input type="text" name="neighborhood" placeholder="المندوب" value={formData.neighborhood} onChange={handleChange} required style={styles.input} />
        <textarea name="notes" placeholder="ملاحظات (اختياري)" value={formData.notes} onChange={handleChange} style={{ ...styles.input, height: '80px' }}></textarea>

        <button type="submit" style={styles.button} disabled={loading}>
          {loading ? 'جارٍ الإضافة...' : 'إضافة'}
        </button>
        <button type="button" onClick={handleBack} style={styles.backButton}>
          الرجوع إلى قائمة المستفيدين
        </button>
      </form>
    </div>
  );
};

const styles = {
  container: {
    padding: '20px',
    direction: 'rtl',
    fontFamily: 'Arial, sans-serif',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '100vh',
    boxSizing: 'border-box',
    backgroundColor: '#f9f9f9',
    flexDirection: 'column',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '15px',
    width: '100%',
    maxWidth: '600px',
    margin: '0 auto',
  },
  input: {
    padding: '12px',
    fontSize: '16px',
    borderRadius: '8px',
    border: '1px solid #ccc',
    width: '100%',
    boxSizing: 'border-box',
  },
  button: {
    padding: '12px',
    backgroundColor: '#004e92',
    color: 'white',
    fontSize: '16px',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    width: '100%',
  },
  backButton: {
    padding: '10px',
    backgroundColor: '#888',
    color: 'white',
    fontSize: '14px',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    width: '100%',
  },
};

const responsiveStyle = `
  @media (max-width: 480px) {
    input, textarea, select, button {
      font-size: 14px !important;
      padding: 10px !important;
    }
    h2 {
      font-size: 20px !important;
      text-align: center;
    }
  }
`;

export default AddResident;
