require('dotenv').config();

const express = require('express');
const nodemailer = require('nodemailer');
const bodyParser = require('body-parser');
const axios = require('axios');
const path = require('path');

const app = express();
const port = 3000;

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
  const timestamp = new Date().toISOString().replace(/[-T:.Z]/g, '').slice(0, 14); 
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

  try {
    const response = await axios.get(
      'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials',
      {
        headers: { Authorization: `Basic ${auth}` }
      }
    );
    console.log('Access Token:', response.data.access_token);
    return response.data.access_token;
  } catch (error) {
    console.error('Failed to get access token:', error.message);
    throw new Error('Could not get M-Pesa access token');
  }
}

// M-Pesa: Initiate STK Push 
async function initiateStkPush(phoneNumber, amount) {
  const token = await getAccessToken();
  const { password, timestamp } = generateMpesaPassword();

  const headers = {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json'
  };

  const payload = {
    BusinessShortCode: process.env.MPESA_LIPA_SHORTCODE,
    Password: password,
    Timestamp: timestamp,
    TransactionType: 'CustomerPayBillOnline',
    Amount: amount,
    PartyA: phoneNumber,
    PartyB: process.env.MPESA_LIPA_SHORTCODE,
    PhoneNumber: phoneNumber,
    CallBackURL: 'https://yourdomain.com/callback', // Change before production
    AccountReference: `Booking #${Date.now()}`,
    TransactionDesc: 'Payment for room booking',
  };

  try {
    const response = await axios.post(
      'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials',
      payload,
      { headers }
    );
    console.log('M-Pesa STK Push Response:', response.data);
    return response.data;
  } catch (error) {
    console.error(
      'M-Pesa STK Push Error:',
      error.response ? error.response.data : error
    );
    throw new Error('M-Pesa STK Push failed');
  }
}

//  API Routes 

// Send booking confirmation email
app.post('/sendConfirmationEmail', (req, res) => {
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

  transporter.sendMail(mailOptions, (error) => {
    if (error) {
      console.error('Email sending error:', error);
      return res.status(500).json({ success: false, message: 'Error sending email' });
    }
    res.status(200).json({ success: true, message: 'Confirmation email sent' });
  });
});

// Initiate M-Pesa payment
app.post('/initiate-payment', async (req, res) => {
  const { phoneNumber, amount } = req.body;
  try {
    const paymentResponse = await initiateStkPush(phoneNumber, amount);
    res.json(paymentResponse);
  } catch (error) {
    res.status(500).json({ status: 'error', message: 'Failed to initiate payment' });
  }
});

// M-Pesa Callback handler
app.post('/callback', (req, res) => {
  const paymentData = req.body;
  console.log('Payment Callback Response:', paymentData);

  if (paymentData.ResultCode === 0) {
    console.log('Payment was successful!');
    // Update booking status or send confirmation email
  } else {
    console.log('Payment failed or was canceled.');
  }

  res.status(200).send('Payment processed');
});

// Start the Server
app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});
