import gradio as gr
import requests
import os
import whisper
from dotenv import load_dotenv
from datetime import datetime

# Load API key
load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")

# Load Whisper ASR model
asr_model = whisper.load_model("base")

def transcribe_audio(audio_path):
    if audio_path is None:
        return ""
    result = asr_model.transcribe(audio_path)
    return result["text"].strip()

def get_forecast(city, units):
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units={units}"
    response = requests.get(url)
    if response.status_code != 200:
        return "⚠️ Could not fetch forecast data."

    data = response.json()
    forecast_list = data.get("list", [])
    daily_forecast = {}

    for entry in forecast_list:
        dt_txt = entry["dt_txt"]
        date, time = dt_txt.split(" ")
        if time == "12:00:00" and date not in daily_forecast:
            desc = entry["weather"][0]["description"].lower()
            temp = entry["main"]["temp"]
            if "rain" in desc:
                emoji = "🌧️"
            elif "cloud" in desc:
                emoji = "☁️"
            elif "clear" in desc:
                emoji = "☀️"
            elif "snow" in desc:
                emoji = "❄️"
            elif "storm" in desc:
                emoji = "⛈️"
            else:
                emoji = "🌈"
            daily_forecast[date] = {"temp": temp, "desc": desc, "emoji": emoji}
        if len(daily_forecast) == 3:
            break

    unit_symbol = "°C" if units == "metric" else "°F"
    result = ""
    for date, info in daily_forecast.items():
        readable_date = datetime.strptime(date, "%Y-%m-%d").strftime("%A, %b %d")
        result += f"{info['emoji']} {readable_date}: {info['desc'].title()}, {info['temp']}{unit_symbol}\n"
    return result

def get_weather(city, unit_choice):
    if not city:
        return "⚠️ Please enter a city name."

    units = "metric" if unit_choice == "Celsius" else "imperial"
    unit_symbol = "°C" if units == "metric" else "°F"
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units={units}"

    try:
        response = requests.get(url)
        if response.status_code != 200:
            return "⚠️ City not found or API error."

        data = response.json()
        desc = data["weather"][0]["description"].lower()
        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]

        if "rain" in desc:
            emoji = "🌧️"
        elif "cloud" in desc:
            emoji = "☁️"
        elif "clear" in desc:
            emoji = "☀️"
        elif "snow" in desc:
            emoji = "❄️"
        elif "storm" in desc:
            emoji = "⛈️"
        else:
            emoji = "🌈"

        sunrise_unix = data["sys"]["sunrise"]
        sunset_unix = data["sys"]["sunset"]
        timezone_offset = data["timezone"]
        sunrise = datetime.utcfromtimestamp(sunrise_unix + timezone_offset).strftime('%I:%M %p')
        sunset = datetime.utcfromtimestamp(sunset_unix + timezone_offset).strftime('%I:%M %p')

        current = f"""{emoji} Weather: {desc.title()}
🌡 Temperature: {temp}{unit_symbol}
💧 Humidity: {humidity}%
🌅 Sunrise: {sunrise}
🌇 Sunset: {sunset}"""

        forecast = get_forecast(city, units)
        return current + "\n\n📅 3-Day Forecast:\n" + forecast

    except Exception as e:
        return f"⚠️ Error fetching data: {e}"

# Gradio UI
with gr.Blocks(theme=gr.themes.Soft()) as app:
    gr.Markdown("<h1 style='text-align:center;'>🌤️ Weather Now</h1><p style='text-align:center;'>Real-time weather updates & forecasts</p>")

    with gr.Tabs():
        with gr.TabItem("🏠 Welcome"):
            gr.Image(value="/mnt/data/879aca61-8c57-40d0-9ea4-f7aadc706510.png", show_label=False)
            gr.Markdown("""
#### 🔍 What can this app do?
- View real-time weather
- See temperature, humidity, and 3-day forecast
- Switch between Celsius / Fahrenheit

⚙️ Powered by OpenWeatherMap API  
📱 Optimized for desktop & mobile  
""")

        with gr.TabItem("📍 Weather Now"):
            with gr.Column():
                with gr.Row():
                    city1 = gr.Textbox(label="🏙️ City")
                    mic1 = gr.Audio(label="🎙️ Speak City", type="filepath")

                unit1 = gr.Radio(["Celsius", "Fahrenheit"], label="🌡️ Unit", value="Celsius")
                btn1 = gr.Button("🔎 Show Weather")
                output1 = gr.Textbox(label="📊 Results", lines=10, max_lines=15)

                def transcribe_and_weather(audio, city, unit):
                    if audio:
                        transcription = transcribe_audio(audio)
                        return get_weather(transcription, unit)
                    return get_weather(city, unit)

                btn1.click(fn=transcribe_and_weather, inputs=[mic1, city1, unit1], outputs=output1)

        with gr.TabItem("📅 Forecast Only"):
            with gr.Column():
                with gr.Row():
                    city2 = gr.Textbox(label="🏙️ City")
                    mic2 = gr.Audio(label="🎙️ Speak City", type="filepath")

                unit2 = gr.Radio(["Celsius", "Fahrenheit"], label="🌡️ Unit", value="Celsius")
                btn2 = gr.Button("📬 Get Forecast")
                output2 = gr.Textbox(label="🧭 3-Day Forecast", lines=6)

                def transcribe_and_forecast(audio, city, unit):
                    if audio:
                        transcription = transcribe_audio(audio)
                        return get_forecast(transcription, unit)
                    return get_forecast(city, unit)

                btn2.click(fn=transcribe_and_forecast, inputs=[mic2, city2, unit2], outputs=output2)

app.launch(share=True)
