document.getElementById('proceedToPayment').addEventListener('click', async function () {
  const email = document.getElementById('email').value;
  const roomType = document.getElementById('roomType').value;
  const timeSlot = document.getElementById('timeSlot').value;
  const phoneNumber = document.getElementById('phoneNumber').value;
  const amount = document.getElementById('amount').value;

  if (!email || !roomType || !timeSlot || !phoneNumber || !amount) {
    alert('Please fill in all required fields.');
    return;
  }

  try {
    // Send confirmation email
    const emailResponse = await fetch('/sendConfirmationEmail', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, roomType, timeSlot })
    });
    const emailData = await emailResponse.json();

    if (!emailData.success) {
      alert('Failed to send confirmation email.');
      return;
    }

    alert('Confirmation email sent successfully! Proceeding to payment...');

    // Initiate M-Pesa payment
    const paymentResponse = await fetch('/initiate-payment', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phoneNumber, amount })
    });
    const paymentData = await paymentResponse.json();

    console.log('Payment initiation response:', paymentData);

    if (paymentData.ResponseCode === '0') {
      alert('Payment request sent to your phone. Please check your M-Pesa prompt.');
      window.location.href = 'payment.html';
    } else {
      alert('Failed to initiate M-Pesa payment.');
    }

  } catch (error) {
    console.error('Error:', error);
    alert('Something went wrong. Please try again.');
  }
});
