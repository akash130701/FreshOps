# 🥬 FreshOps

FreshOps is a Streamlit-based web app that helps you plan weekly fruit and vegetable consumption so you finish everything before it spoils.

Add your produce, specify quantities and shelf life, and FreshOps generates an optimized Monday to Sunday schedule that spreads usage evenly in whole units.

---

## 🚀 Features

* Add fruits, vegetables, and herbs with total quantity
* Choose shelf life from:

  * Built-in produce database (typical storage estimates)
  * Custom number of days
* Automatically distributes consumption evenly before expiry
* Whole-unit planning (no fractional quantities)
* Clean weekly calendar view (Mon–Sun)
* Smart name matching with fuzzy search and suggestions

---

## 🧠 How It Works

For each item:

1. Shelf life is interpreted as the number of days from Monday.

   * 1 = Monday only
   * 7 = Entire week
   * Values above 7 are capped to the current week

2. The optimization model:

   * Ensures total scheduled quantity equals your input quantity
   * Distributes consumption as evenly as possible across valid days
   * Uses integer values only

The result is a practical daily plan that minimizes waste and avoids uneven spikes in consumption.

---

## 📦 Using the App

### 1️⃣ Add Produce

In the sidebar:

* Enter the name (e.g. Spinach, Apples, Capsicum)
* Enter total quantity (your chosen unit)
* Select shelf life mode:

  * **Database**: Uses built-in estimates
  * **Custom**: Enter your own number of days

Click **Add item**.

---

### 2️⃣ Generate Schedule

After adding items:

* Click **Generate schedule**
* The weekly calendar will display daily quantities
* A totals check confirms everything sums correctly

---

### 3️⃣ Interpret the Calendar

* Columns represent days (Mon–Sun)
* Rows represent each produce item
* Weekend columns are lightly highlighted
* “Daily total” row shows total consumption per day

---

## 🗂 Shelf Life Database

The built-in database includes common fruits, vegetables, herbs, and global produce variants.

Estimates are based on typical home storage conditions and are intended for planning purposes only. Always follow food safety guidance and packaging instructions.

---

## ⚙️ Running Locally

1. Clone the repository:

   ```
   git clone <your-repo-url>
   cd freshops
   ```

2. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

3. Run the app:

   ```
   streamlit run app.py
   ```

---

## 🌍 Deployment

FreshOps can be deployed easily via:

* Streamlit Community Cloud
* Render
* Railway

Simply connect your GitHub repository and specify `app.py` as the entry point.

---

## 🎯 Use Cases

* Weekly meal planning
* Reducing food waste
* Student or shared-house grocery management
* Household produce optimization

---

## ⚠️ Disclaimer

Shelf life values are approximate planning estimates. They are not medical or food-safety advice. Actual storage life depends on ripeness, storage conditions, and handling.

---

Built with Streamlit and PuLP. And Cursor
