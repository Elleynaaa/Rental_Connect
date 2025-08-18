require('dotenv').config();

const express = require('express');
const nodemailer = require('nodemailer');
const bodyParser = require('body-parser');
const axios = require('axios');
const path = require('path');

const app = express();
const port = process.env.PORT || 3000;

// Middleware
app.use(bodyParser.json());

// Serve static files (HTML, CSS, JS, images) from "public" folder
app.use(express.static(path.join(__dirname, 'public')));

// Default route to serve index.html
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Nodemailer Transporter (for confirmation emails)
const transporter = nodemailer.createTransport({
  service: 'gmail',
  auth: {
    user: process.env.EMAIL_USER,
    pass: process.env.EMAIL_PASS
  }
});

// Function to generate M-Pesa password dynamically
function generateMpesaPassword() {
  const timestamp = new Date().toISOString().replace(/[-T:.Z]/g, '').slice(0, 14); // yyyyMMddHHmmss
  const password = Buffer.from(
    process.env.MPESA_LIPA_SHORTCODE + process.env.MPESA_PASSKEY + timestamp
  ).toString('base64');

  return { password, timestamp };
}

// M-Pesa: Get Access Token
async function getAccessToken() {
  const auth = Buffer.from(
    `${process.env.MPESA_LIPA_KEY}:${process.env.MPESA_LIPA_SECRET}`
  ).toString('base64');

  const url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials';

  const res = await axios.get(url, {
    headers: { Authorization: `Basic ${auth}` }
  });

  console.log("✅ Access Token App Key/Secret used:", process.env.MPESA_LIPA_KEY, process.env.MPESA_LIPA_SECRET);
  return res.data.access_token;
}


// M-Pesa: Initiate STK Push (now includes boo)
async function initiateStkPush(phoneNumber, amount, bookingId, email) {
  const token = await getAccessToken();
  const { password, timestamp } = generateMpesaPassword();

  const payload = {
    BusinessShortCode: process.env.MPESA_LIPA_SHORTCODE,
    Password: password,
    Timestamp: timestamp,
    TransactionType: 'CustomerPayBillOnline',
    Amount: amount,
    PartyA: phoneNumber,
    PartyB: process.env.MPESA_LIPA_SHORTCODE,
    PhoneNumber: phoneNumber,
    CallBackURL: process.env.MPESA_CALLBACK_URL,
    AccountReference: `BOOKING_${bookingId}_${email}`,
    TransactionDesc: 'Payment for room booking',
  };

  console.log("👉 Sending STK Payload:", payload);

  const res = await axios.post(
    'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest',
    payload,
    {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }
  );

  return res.data;
}

/* ---------------- API ROUTES ---------------- */

// Send booking confirmation email
app.post('/sendConfirmationEmail', async (req, res) => {
  try {
    const { email, roomType, timeSlot } = req.body;

    const mailOptions = {
      from: process.env.EMAIL_USER,
      to: email,
      subject: 'Booking Confirmation',
      text: `Dear customer,

Your booking for a ${roomType} has been confirmed for the time slot: ${timeSlot}.

Thank you for choosing us!

Best regards,
Your Hotel Name`
    };

    await transporter.sendMail(mailOptions);
    res.status(200).json({ success: true, message: 'Confirmation email sent' });
  } catch (err) {
    console.error('Email sending error:', err);
    res.status(500).json({ success: false, message: 'Error sending email' });
  }
});

// Initiate M-Pesa payment (validate tenant email via Django)
app.post('/initiate-payment', async (req, res) => {
  try {
    const { phoneNumber, amount, bookingId, email, token } = req.body;

    // ✅ Step 1: Verify tenant with Django using JWT token
    let verifiedEmail = email;
    if (token) {
      try {
        const verifyRes = await axios.get(
          'http://127.0.0.1:8000/api/tenants/', // adjust to /api/user/profile/ if you have it
          { headers: { Authorization: `Bearer ${token}` } }
        );

        if (verifyRes.data && verifyRes.data.length > 0) {
          verifiedEmail = verifyRes.data[0].user.email;
        }
      } catch (err) {
        console.warn('⚠️ Could not verify tenant from Django, falling back to provided email');
      }
    }

    // ✅ Step 2: Proceed with STK push using the verified email
    const paymentResponse = await initiateStkPush(phoneNumber, amount, bookingId, verifiedEmail);

    res.json({
      ...paymentResponse,
      bookingId,
      email: verifiedEmail
    });
  } catch (error) {
    console.error('STK Push error:', error?.response?.data || error.message);
    res.status(500).json({ status: 'error', message: 'Failed to initiate payment' });
  }
});

// M-Pesa Callback handler (from Safaricom)
app.post('/callback', async (req, res) => {
  try {
    console.log('📥 Raw callback:', JSON.stringify(req.body, null, 2));

    const stkCallback = req.body?.Body?.stkCallback;
    if (!stkCallback) {
      console.error('Invalid callback payload');
      return res.status(200).json({ message: 'Received (invalid payload)' });
    }

    const resultCode = stkCallback.ResultCode;
    const resultDesc = stkCallback.ResultDesc;

    let amount = null;
    let mpesaReceipt = null;
    let phoneNumber = null;
    let transactionDate = null;
    let accountRef = stkCallback?.MerchantRequestID || ''; // fallback

    const items = stkCallback.CallbackMetadata?.Item || [];
    for (const item of items) {
      if (item.Name === 'Amount') amount = item.Value;
      if (item.Name === 'MpesaReceiptNumber') mpesaReceipt = item.Value;
      if (item.Name === 'PhoneNumber') phoneNumber = item.Value;
      if (item.Name === 'TransactionDate') transactionDate = item.Value;
      if (item.Name === 'AccountReference') accountRef = item.Value;
    }

    // Extract bookingId + email from "BOOKING_1234_email"
    let bookingId = null;
    let email = null;
    if (accountRef && accountRef.startsWith('BOOKING_')) {
      const parts = accountRef.split('_');
      bookingId = parts[1];
      email = parts.slice(2).join('_'); // handles underscores in email
    }

    // Forward to Django
    await axios.post('http://localhost:8000/api/payments/callback/', {
      booking_id: bookingId,
      email: email,
      result_code: resultCode,
      result_desc: resultDesc,
      amount,
      mpesa_receipt: mpesaReceipt,
      phone_number: phoneNumber,
      transaction_date: transactionDate,
      raw_callback: req.body
    });

    res.status(200).json({ message: 'Callback received' });
  } catch (err) {
    console.error('❌ Error handling callback:', err?.response?.data || err.message);
    res.status(200).json({ message: 'Callback processed with errors' });
  }
});

// Start the Server
app.listen(port, () => {
  console.log(`🚀 Server is running on port ${port}`);
});