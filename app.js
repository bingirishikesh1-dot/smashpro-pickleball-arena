const gameSelect = document.querySelector("#game");
const dateInput = document.querySelector("#booking-date");
const timeSelect = document.querySelector("#booking-time");
const priceOutput = document.querySelector("#booking-price");
const bookingForm = document.querySelector("#booking-form");
const formMessage = document.querySelector("#form-message");
const adminWhatsAppNumber = "919603813946";

function localDateString(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function refreshPrice() {
  const day = dateInput.value ? new Date(`${dateInput.value}T12:00:00`).getDay() : new Date().getDay();
  const price = gameSelect.value === "paddleball" ? 2000 : (day === 0 || day === 6 ? 600 : 400);
  priceOutput.textContent = `₹${price.toLocaleString("en-IN")}`;
}

function populateTimes() {
  const previousValue = timeSelect.value;
  timeSelect.replaceChildren();
  for (let hour = 6; hour < 23; hour += 1) {
    const option = document.createElement("option");
    option.value = `${String(hour).padStart(2, "0")}:00`;
    const suffix = hour < 12 ? "AM" : "PM";
    const displayHour = hour % 12 || 12;
    option.textContent = `${displayHour}:00 ${suffix}`;
    timeSelect.append(option);
  }
  if (previousValue) timeSelect.value = previousValue;
  if (!timeSelect.value) timeSelect.selectedIndex = 0;
}

dateInput.min = localDateString(new Date());
dateInput.value = dateInput.min;
document.querySelector("#year").textContent = new Date().getFullYear();
populateTimes();
refreshPrice();
gameSelect.addEventListener("change", refreshPrice);
dateInput.addEventListener("change", refreshPrice);

bookingForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!bookingForm.reportValidity()) return;

  formMessage.classList.remove("error");
  const booking = Object.fromEntries(new FormData(bookingForm).entries());
  const gameName = booking.game === "paddleball" ? "Paddleball" : "Pickleball";
  const submitButton = bookingForm.querySelector("button[type='submit']");
  submitButton.disabled = true;
  formMessage.textContent = "Saving your request…";

  try {
    const response = await fetch("/api/bookings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(booking),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Booking could not be saved. Please try again.");

    const whatsappMessage = [
      "New SmashPro booking request",
      `Name: ${booking.name}`,
      `Phone: ${booking.phone}`,
      `Game: ${gameName}`,
      `Date: ${booking.date}`,
      `Start time: ${booking.time}`,
      "Duration: 1 hour",
      `Price: ₹${result.priceInr.toLocaleString("en-IN")}`,
      "Paddle and ball included.",
    ].join("\n");

    formMessage.textContent = "Opening WhatsApp. Tap Send there to send your booking details.";
    window.location.href = `https://wa.me/${adminWhatsAppNumber}?text=${encodeURIComponent(whatsappMessage)}`;
  } catch (error) {
    formMessage.textContent = error.message || "Booking could not be saved. Please try again.";
    formMessage.classList.add("error");
    submitButton.disabled = false;
  }
});
