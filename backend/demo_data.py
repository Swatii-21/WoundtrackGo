"""Demo patients and visits. Delete once the real database is connected."""
PATIENTS = [
    dict(id=1, name="Priya Sharma", age=62, gender="Female", dx="DFU", full="Diabetic Foot Ulcer", loc="Right Foot", risk="High"),
    dict(id=2, name="Rajesh Kumar", age=58, gender="Male", dx="VLU", full="Venous Leg Ulcer", loc="Left Ankle", risk="Medium"),
    dict(id=3, name="Anita Verma", age=67, gender="Female", dx="Pressure Ulcer", full="Pressure Ulcer", loc="Sacrum", risk="Low"),
    dict(id=4, name="Sanjay Mehta", age=55, gender="Male", dx="DFU", full="Diabetic Foot Ulcer", loc="Left Foot", risk="Medium"),
]
def V(date, pct, g, s, n, grade, conf): return dict(date=date, pct=pct, px=int(pct / 100 * 100400), gran=g, fibrin=s, callus=n, grade=grade, conf=conf)
VISITS = {
    1: [V("10 Oct 2025", 20, 38, 40, 22, 1, 90.1), V("20 Oct 2025", 17, 45, 38, 17, 1, 91.4), V("28 Oct 2025", 14.5, 50, 35, 15, 2, 92.0), V("05 Nov 2025", 12.4, 55, 30, 15, 2, 92.7)],
    2: [V("14 Oct 2025", 9, 60, 30, 10, 1, 88.0), V("03 Nov 2025", 7.5, 66, 26, 8, 1, 89.5)],
    3: [V("12 Oct 2025", 6, 70, 22, 8, 1, 90.0), V("28 Oct 2025", 4.8, 75, 18, 7, 1, 91.0)],
    4: [V("02 Oct 2025", 11, 48, 36, 16, 2, 87.0), V("25 Oct 2025", 10.2, 50, 35, 15, 2, 88.0)],
}
