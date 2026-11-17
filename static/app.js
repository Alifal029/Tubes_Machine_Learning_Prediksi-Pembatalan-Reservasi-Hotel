document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("predictionForm");
  const statusText = document.getElementById("status");
  const resultBox = document.getElementById("result");
  const errorBox = document.getElementById("error");
  const submitBtn = document.getElementById("submitBtn");

  const predictionText = document.getElementById("prediction");
  const resultBadge = document.getElementById("resultBadge");
  const probabilityCancel = document.getElementById("probabilityCancel");
  const probabilityNotCancel = document.getElementById("probabilityNotCancel");
  const probBar = document.getElementById("probBar");
  const disclaimerText = document.getElementById("disclaimer");

  const numericFields = [
    "lead_time",
    "stays_in_weekend_nights",
    "stays_in_week_nights",
    "adults",
    "children",
  ];

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());

    // Konversi field numerik menjadi number
    numericFields.forEach((field) => {
      payload[field] = Number(payload[field]);
    });

    statusText.textContent = "Mengirim data ke model Machine Learning...";
    resultBox.hidden = true;
    errorBox.hidden = true;
    submitBtn.disabled = true;

    try {
      const response = await fetch("/predict", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Accept": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (!response.ok) {
        let errorMsg = "Terjadi kesalahan pada request.";
        if (Array.isArray(data.detail)) {
          errorMsg = data.detail
            .map((item) => `${item.loc ? item.loc.join(".") : "field"}: ${item.msg}`)
            .join("; ");
        } else if (typeof data.detail === "string") {
          errorMsg = data.detail;
        }
        throw new Error(errorMsg);
      }

      // Render hasil prediksi
      const isCanceled = data.is_canceled;
      predictionText.textContent = data.prediction;

      resultBox.classList.remove("canceled", "not-canceled");
      resultBadge.classList.remove("canceled", "not-canceled");
      probBar.classList.remove("canceled", "not-canceled");

      if (isCanceled) {
        resultBox.classList.add("canceled");
        resultBadge.classList.add("canceled");
        resultBadge.textContent = "Risiko Batal";
        probBar.classList.add("canceled");
      } else {
        resultBox.classList.add("not-canceled");
        resultBadge.classList.add("not-canceled");
        resultBadge.textContent = "Reservasi Aman";
        probBar.classList.add("not-canceled");
      }

      const cancelProb = data.probability_cancel !== null ? (data.probability_cancel * 100).toFixed(2) : null;
      const notCancelProb = data.probability_not_cancel !== null ? (data.probability_not_cancel * 100).toFixed(2) : null;

      probabilityCancel.textContent = cancelProb !== null ? `${cancelProb}%` : "N/A";
      probabilityNotCancel.textContent = notCancelProb !== null ? `${notCancelProb}%` : "N/A";

      if (cancelProb !== null) {
        probBar.style.width = `${cancelProb}%`;
      } else {
        probBar.style.width = "0%";
      }

      disclaimerText.textContent = data.disclaimer || "";

      resultBox.hidden = false;
      statusText.textContent = "Prediksi berhasil dihitung.";
    } catch (err) {
      errorBox.textContent = `Gagal memproses prediksi: ${err.message}`;
      errorBox.hidden = false;
      statusText.textContent = "Request gagal.";
    } finally {
      submitBtn.disabled = false;
    }
  });

  form.addEventListener("reset", () => {
    resultBox.hidden = true;
    errorBox.hidden = true;
    statusText.textContent = "Form telah direset ke nilai bawaan. Siap untuk prediksi baru.";
  });
});
