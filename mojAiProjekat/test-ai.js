const { GoogleGenerativeAI } = require("@google/generative-ai");

async function run() {
  // Postavi svoj ključ
  const genAI = new GoogleGenerativeAI("AIzaSyDY8pwx51y0lK4pq9uemG1WzAr1kntaILA");
  
  // U 2026. godini koristimo 'gemini-1.5-flash-latest' ili 'gemini-2.0-flash'
  // v1beta putanja je neophodna za najnovije Flash modele
  const model = genAI.getGenerativeModel(
    { model: "gemini-1.5-flash-latest" }, 
    { apiVersion: 'v1beta' }
  );

  try {
    console.log("Povezivanje sa Google AI (v1beta)...");
    const result = await model.generateContent("Napiši samo: USPEŠNO POVEZANO.");
    const response = await result.response;
    console.log("ODGOVOR:", response.text());
  } catch (error) {
    console.error("GREŠKA:", error.message);
    console.log("\nSavet: Proveri svoj region u Google AI Studio. Ako si u EU, možda je potreban poseban pristup.");
  }
}

run();

