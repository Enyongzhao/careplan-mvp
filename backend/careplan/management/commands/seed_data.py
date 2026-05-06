from django.core.management.base import BaseCommand
from careplan.models import Patient, Provider, Order, CarePlan
from datetime import date


PATIENTS = [
    {"first_name": "James",   "last_name": "Hartwell",  "mrn": "MRN-001", "date_of_birth": date(1952, 3, 14)},
    {"first_name": "Maria",   "last_name": "Delgado",   "mrn": "MRN-002", "date_of_birth": date(1968, 7, 22)},
    {"first_name": "Robert",  "last_name": "Chen",      "mrn": "MRN-003", "date_of_birth": date(1945, 11, 5)},
    {"first_name": "Linda",   "last_name": "Okafor",    "mrn": "MRN-004", "date_of_birth": date(1975, 1, 30)},
    {"first_name": "William", "last_name": "Nakamura",  "mrn": "MRN-005", "date_of_birth": date(1960, 9, 18)},
]

PROVIDERS = [
    {"name": "Dr. Sarah Patel",   "npi": "1234567890"},
    {"name": "Dr. Marcus Webb",   "npi": "2345678901"},
    {"name": "Dr. Elena Sousa",   "npi": "3456789012"},
]

# (patient_index, provider_index, order data)
ORDERS = [
    # James Hartwell — CHF + Type 2 DM
    (0, 0, {
        "medication_name": "Furosemide 40mg",
        "primary_diagnosis": "Chronic Heart Failure (I50.9) — reduced ejection fraction, NYHA Class III. Patient reports progressive dyspnea on exertion and bilateral lower extremity edema over the past 3 weeks.",
        "additional_diagnoses": "Type 2 Diabetes Mellitus (E11.9); Hypertension (I10); CKD Stage 2 (N18.2)",
        "medication_history": "Metformin 1000mg BID (ongoing); Lisinopril 10mg QD (ongoing); Atorvastatin 40mg QD (ongoing); Aspirin 81mg QD (ongoing). Prior loop diuretic use 2019–2021, discontinued due to hypokalemia.",
        "patient_records": "Echo (2025-11): EF 35%, moderate MR. BMP (2026-04): K+ 3.8, Cr 1.4, BUN 22. BNP 820 pg/mL. Recent weight gain 4 lbs over 1 week. BP 148/92 on last visit. BMI 31.2.",
    }),
    (0, 1, {
        "medication_name": "Jardiance (Empagliflozin) 10mg",
        "primary_diagnosis": "Type 2 Diabetes Mellitus with cardiovascular risk (E11.65). HbA1c 8.4% at last check. Patient interested in SGLT2 inhibitor for dual glycemic and cardiac benefit.",
        "additional_diagnoses": "Chronic Heart Failure (I50.9); Hypertension (I10); Obesity (E66.9)",
        "medication_history": "Metformin 1000mg BID; Furosemide 40mg QD (newly started); Lisinopril 10mg QD; Atorvastatin 40mg QD. No prior SGLT2i use. No sulfa allergy.",
        "patient_records": "HbA1c 8.4% (2026-03). eGFR 58 mL/min — SGLT2i eligible. Urinalysis: no active infection. BP 148/92. Cardiologist cleared for SGLT2i initiation. BMI 31.2.",
    }),

    # Maria Delgado — Asthma + GERD
    (1, 1, {
        "medication_name": "Fluticasone/Salmeterol (Advair) 250/50 mcg",
        "primary_diagnosis": "Moderate persistent asthma (J45.40). Patient reports 3–4 daytime symptoms per week and nocturnal awakening twice weekly. Last exacerbation required ED visit 6 months ago.",
        "additional_diagnoses": "Allergic Rhinitis (J30.9); GERD (K21.0); Anxiety Disorder (F41.1)",
        "medication_history": "Albuterol 90mcg PRN (using 5–6x/week, overuse); Cetirizine 10mg QD; Omeprazole 20mg QD. Previous ICS: Budesonide 180mcg — poor adherence due to taste. No oral corticosteroid use in past 12 months.",
        "patient_records": "Spirometry (2026-02): FEV1 72% predicted, FEV1/FVC 0.68, 15% reversibility post-bronchodilator. Peak flow diary: highly variable. Skin prick: positive cat, dust mite, grass. FeNO 38 ppb (elevated). BMI 24.1.",
    }),
    (1, 2, {
        "medication_name": "Omeprazole 40mg",
        "primary_diagnosis": "Gastroesophageal Reflux Disease with esophagitis (K21.0). Patient describes heartburn daily, worse when lying flat, with occasional regurgitation. Symptoms poorly controlled on 20mg dose.",
        "additional_diagnoses": "Moderate persistent asthma (J45.40); Hiatal Hernia (K44.9)",
        "medication_history": "Omeprazole 20mg QD (inadequate symptom control); Albuterol PRN; Fluticasone/Salmeterol newly initiated. No H2-blocker history. No NSAID use.",
        "patient_records": "Upper endoscopy (2025-09): Los Angeles Grade B esophagitis, small sliding hiatal hernia. H. pylori rapid urease test negative. No Barrett's changes. Symptom score (GERD-Q): 12/18. Weight stable.",
    }),

    # Robert Chen — COPD + Atrial Fibrillation
    (2, 2, {
        "medication_name": "Tiotropium (Spiriva) 18mcg inhaled QD",
        "primary_diagnosis": "COPD, severe (J44.1) — Gold Stage III. 45 pack-year smoking history, quit 2018. Reports chronic productive cough, significant exertional dyspnea, 2 exacerbations in past year.",
        "additional_diagnoses": "Atrial Fibrillation (I48.91); OSA on CPAP (G47.33); Osteoporosis (M81.0)",
        "medication_history": "Albuterol/Ipratropium MDI PRN; Prednisone 40mg for last exacerbation (2026-01); Rivaroxaban 20mg QD; Diltiazem 120mg QD for rate control; Calcium + Vit D supplementation. No current LAMA.",
        "patient_records": "Spirometry (2026-01): FEV1 42% predicted, FEV1/FVC 0.52. 6MWT: 280 m (severely limited). CT Chest (2025-11): emphysematous changes upper lobes, no mass. O2 Sat 91% at rest. MMRC dyspnea scale 3/4. BMI 21.8.",
    }),
    (2, 0, {
        "medication_name": "Rivaroxaban 20mg",
        "primary_diagnosis": "Non-valvular Atrial Fibrillation (I48.91) — persistent, rate-controlled. CHA2DS2-VASc score 4. Anticoagulation continued for stroke prevention.",
        "additional_diagnoses": "COPD (J44.1); Hypertension (I10); CKD Stage 1 (N18.1)",
        "medication_history": "Previously on Warfarin — switched to Rivaroxaban 2023 due to labile INR. Diltiazem 120mg QD; Tiotropium newly added. HAS-BLED score 2. No recent bleeding events.",
        "patient_records": "ECG (2026-03): AF with ventricular rate 78 bpm, no delta waves. ECHO: EF 55%, LA mildly dilated. Cr 1.1, eGFR 72 — dose appropriate. CBC: Hgb 13.2. INR not monitored (on DOAC). BP 132/80.",
    }),

    # Linda Okafor — Migraine + Hypothyroidism
    (3, 0, {
        "medication_name": "Topiramate 50mg BID (prophylaxis)",
        "primary_diagnosis": "Chronic migraine (G43.709) — 15+ headache days/month for >3 months. Patient reports severe unilateral pulsating headaches with photophobia, phonophobia, and nausea. Significant functional impairment.",
        "additional_diagnoses": "Hypothyroidism (E03.9); Depression (F32.1); Insomnia (G47.00)",
        "medication_history": "Sumatriptan 100mg PRN (using 10–12x/month — MOH risk); Sertraline 50mg QD; Levothyroxine 75mcg QD. Prior prophylaxis: Amitriptyline 25mg — discontinued due to weight gain. No beta-blocker use.",
        "patient_records": "MIDAS score 24 (severe disability). Headache diary: 18 days/month, average pain 7/10. TSH 2.1 mIU/L (stable). MRI Brain (2025-08): no structural abnormality. BMI 27.4. No glaucoma or kidney stones on history.",
    }),
    (3, 1, {
        "medication_name": "Levothyroxine 88mcg QD",
        "primary_diagnosis": "Hypothyroidism (E03.9) — dose adjustment. Patient on 75mcg, TSH now 5.8 mIU/L (above target). Reports fatigue, cold intolerance, and constipation consistent with suboptimal replacement.",
        "additional_diagnoses": "Chronic migraine (G43.709); Depression (F32.1); Iron deficiency anemia (D50.9)",
        "medication_history": "Levothyroxine 75mcg QD (current, insufficient); Sertraline 50mg QD — note potential interaction with absorption; Topiramate 50mg BID (new). Levothyroxine taken with coffee per patient report — counseled on separation from food/caffeine.",
        "patient_records": "TSH 5.8 mIU/L (2026-04), Free T4 0.9 ng/dL (low-normal). Previous TSH on 75mcg: 3.2 (2025-10) — possible adherence or absorption issue. Ferritin 11 ng/mL (low). CBC: mild microcytic anemia. Weight 68 kg.",
    }),

    # William Nakamura — HTN + Hyperlipidemia
    (4, 2, {
        "medication_name": "Amlodipine 10mg QD",
        "primary_diagnosis": "Essential Hypertension (I10) — uncontrolled. BP averaging 162/98 over past 3 visits. Patient reports good adherence but admits high sodium diet. Previous regimen not achieving target <130/80.",
        "additional_diagnoses": "Hyperlipidemia (E78.5); Type 2 Diabetes (E11.9); Peripheral Artery Disease (I73.9)",
        "medication_history": "Lisinopril 20mg QD (BP still not at goal); Hydrochlorothiazide 25mg QD; Atorvastatin 80mg QD; Metformin 500mg BID; Aspirin 81mg QD; Cilostazol 100mg BID. No calcium channel blocker history.",
        "patient_records": "BP log: 158/96, 164/100, 160/97 (last 3 visits). EKG: LVH pattern. Urinalysis: microalbuminuria (ACR 85 mg/g). Cr 1.2, eGFR 64. Lipid panel (2026-03): LDL 72 on statin. ABI 0.78 bilateral. BMI 28.9.",
    }),
    (4, 0, {
        "medication_name": "Atorvastatin 80mg QD",
        "primary_diagnosis": "Mixed Hyperlipidemia (E78.5) with established cardiovascular disease (PAD). Patient at very high CV risk. LDL target <55 mg/dL per ACC/AHA guidelines for ASCVD. Current LDL 72 on 80mg statin.",
        "additional_diagnoses": "Peripheral Artery Disease (I73.9); Essential Hypertension (I10); Type 2 Diabetes (E11.9)",
        "medication_history": "Atorvastatin 80mg QD (ongoing — LDL not yet at goal for very high risk); Ezetimibe not yet tried; No PCSK9 inhibitor history. Lisinopril 20mg; HCTZ 25mg; Aspirin 81mg; Cilostazol 100mg BID. No statin intolerance reported.",
        "patient_records": "Lipid panel (2026-03): Total Chol 168, LDL 72, HDL 38, TG 290. LDL still above 55 mg/dL target for PAD+DM. Hepatic function normal. CK not elevated. ABI 0.78. No claudication change. Vascular surgery follow-up scheduled.",
    }),
]

CARE_PLAN_CONTENT = [
    # James Hartwell — Furosemide
    """CARE PLAN — James Hartwell | MRN-001 | Furosemide 40mg

ASSESSMENT: 72-year-old male with CHF (EF 35%) presenting with decompensation — 4 lb weight gain, worsening edema, BNP 820. Initiation of loop diuretic is appropriate.

PLAN:
1. Start Furosemide 40mg PO QD. Titrate to 80mg if diuresis insufficient after 72h.
2. Daily weights — patient to call clinic if >2 lb gain in 24h or >4 lb in 1 week.
3. Monitor electrolytes (BMP) in 1 week; potassium supplementation if K+ <3.5.
4. Fluid restriction 1.5 L/day; sodium <2g/day dietary counseling.
5. Schedule cardiology follow-up in 2 weeks for repeat echo and medication optimization.
6. Educate on signs of worsening CHF: orthopnea, PND, increased edema.

MONITORING: Weight daily, BMP in 7 days, BNP at follow-up.""",

    # James Hartwell — Jardiance
    """CARE PLAN — James Hartwell | MRN-001 | Jardiance (Empagliflozin) 10mg

ASSESSMENT: Patient with T2DM (HbA1c 8.4%) and CHF. SGLT2 inhibitor indicated for dual benefit — glycemic control and HF hospitalization reduction. eGFR 58 supports initiation.

PLAN:
1. Start Empagliflozin 10mg PO QD with morning meal.
2. Reassess HbA1c in 3 months; consider uptitration to 25mg if glycemic control suboptimal.
3. Counsel on urogenital hygiene — increased UTI/yeast infection risk.
4. Hold medication if patient NPO, severe illness, or undergoing procedures (DKA risk).
5. Monitor renal function: repeat BMP in 4 weeks — modest Cr rise (≤0.3) acceptable.
6. Coordinate with cardiologist — SGLT2i for HF benefit documented.

MONITORING: HbA1c q3 months, BMP in 4 weeks, BP monitoring.""",

    # Maria Delgado — Advair
    """CARE PLAN — Maria Delgado | MRN-002 | Fluticasone/Salmeterol (Advair) 250/50

ASSESSMENT: 57-year-old female with moderate persistent asthma (FEV1 72%), overusing SABA. Stepping up to ICS/LABA combination is indicated per GINA Step 3 guidelines.

PLAN:
1. Start Advair 250/50 one puff BID. Demonstrate proper MDI + spacer technique.
2. Continue Albuterol PRN only — reduce frequency target to ≤2x/week.
3. Rinse mouth after each Advair dose (thrush prevention).
4. Allergen avoidance counseling: dust mite covers, minimize cat exposure.
5. Refer to asthma educator for action plan and peak flow monitoring.
6. Reassess in 4 weeks — if well controlled (FEV1 >80%), maintain; if not, consider add-on LTRA.
7. Note: if GERD worsening, consider reflux as asthma trigger — optimize PPI therapy.

MONITORING: Peak flow diary, symptom log, spirometry in 3 months.""",

    # Maria Delgado — Omeprazole 40mg
    """CARE PLAN — Maria Delgado | MRN-002 | Omeprazole 40mg

ASSESSMENT: GERD with endoscopy-confirmed Grade B esophagitis. Dose escalation from 20mg to 40mg appropriate. Hiatal hernia noted — surgical consult not yet indicated.

PLAN:
1. Increase Omeprazole to 40mg PO QD, 30–60 minutes before breakfast.
2. Lifestyle modifications: elevate HOB 30°, no eating within 3h of bedtime, avoid triggers (caffeine, chocolate, fatty foods, alcohol).
3. Weight maintenance counseling.
4. Repeat upper endoscopy in 8 weeks to confirm esophagitis healing.
5. If symptoms persist at 40mg, consider switching to Pantoprazole or adding H2-blocker at bedtime.
6. Note: Omeprazole may interact with Clopidogrel — not currently on antiplatelet but flag for future.

MONITORING: Symptom diary, endoscopy 8 weeks, TSH if fatigue develops (PPI-thyroid interaction possible).""",

    # Robert Chen — Tiotropium
    """CARE PLAN — Robert Chen | MRN-003 | Tiotropium (Spiriva) 18mcg

ASSESSMENT: 80-year-old male with severe COPD (Gold III, FEV1 42%) and 2 exacerbations in past year. Adding LAMA is consistent with GOLD ABCD Group E management. Currently on SABA/SAMA combination only.

PLAN:
1. Start Tiotropium HandiHaler 18mcg inhaled QD. Provide device training — confirm correct capsule piercing technique.
2. Continue Albuterol/Ipratropium PRN for breakthrough symptoms.
3. Enroll in pulmonary rehabilitation program — evidence-based for FEV1 <50%.
4. Influenza vaccine and pneumococcal (PCV15 + PPSV23) if not up to date.
5. Exacerbation action plan: begin antibiotics + prednisone taper if increased sputum/dyspnea.
6. Review CPAP adherence — OSA management critical for COPD outcomes.
7. Consider adding ICS if eosinophil count >300/μL on next CBC.

MONITORING: Spirometry in 3 months, O2 sat at each visit, 6MWT q6 months.""",

    # Robert Chen — Rivaroxaban
    """CARE PLAN — Robert Chen | MRN-003 | Rivaroxaban 20mg

ASSESSMENT: Persistent AF with CHA2DS2-VASc score 4 — stroke prevention with anticoagulation is mandatory. Dose of 20mg with evening meal appropriate for eGFR 72.

PLAN:
1. Continue Rivaroxaban 20mg PO QD with evening meal (improves absorption by 39%).
2. Reinforce strict adherence — missed dose should be taken same day if remembered; do not double-dose.
3. Fall risk assessment — consider physical therapy given COPD-related deconditioning.
4. Avoid NSAIDs and aspirin (bleeding risk); Tylenol preferred for pain.
5. Monitor for signs of bleeding: unusual bruising, hematuria, black stools — return to ED.
6. Labs: BMP q6 months (renal dosing checkpoint). No routine INR needed.
7. Cardiology to assess rhythm control vs. rate control strategy at next visit.

MONITORING: BMP q6 months, annual CBC, BP control.""",

    # Linda Okafor — Topiramate
    """CARE PLAN — Linda Okafor | MRN-004 | Topiramate 50mg BID (Migraine Prophylaxis)

ASSESSMENT: 51-year-old female with chronic migraine (18 days/month, MIDAS 24). Medication overuse headache risk from frequent triptan use. Topiramate is first-line prophylactic per AHS guidelines.

PLAN:
1. Start Topiramate 25mg QHS × 2 weeks, then increase to 50mg BID (slow titration reduces side effects).
2. Limit Sumatriptan to ≤10 days/month to prevent MOH. Provide headache diary.
3. Counsel on Topiramate side effects: cognitive slowing ("Dopamax"), paresthesias, metabolic acidosis, kidney stones — hydration ≥2L/day.
4. CRITICAL: Topiramate is teratogenic (oral cleft risk) — confirm contraception plan.
5. Sertraline interaction: monitor for serotonin syndrome if using sumatriptan concurrently.
6. Reassess in 8 weeks — expect 50% reduction in headache days within 3 months.
7. Goal: reduce headache days to <8/month over 6 months.

MONITORING: Headache diary monthly, BMP (bicarb) q3 months, weight monitoring.""",

    # Linda Okafor — Levothyroxine
    """CARE PLAN — Linda Okafor | MRN-004 | Levothyroxine 88mcg QD

ASSESSMENT: Hypothyroidism with subtherapeutic TSH 5.8 on 75mcg. Dose escalation to 88mcg appropriate. Likely cause: absorption issue (coffee, timing) rather than primary non-compliance.

PLAN:
1. Increase Levothyroxine to 88mcg PO QD. Take on empty stomach, 30–60 min before food/coffee.
2. Counsel specifically: Sertraline and iron supplements reduce levothyroxine absorption — separate by ≥4 hours.
3. Address iron deficiency: start Ferrous Sulfate 325mg QD (separate from Levothyroxine by ≥4h).
4. Reassess TSH in 6 weeks — target TSH 0.5–2.0 for age and symptom profile.
5. Fatigue may also relate to migraine burden and depression — multidisciplinary approach.
6. If TSH still elevated at 6 weeks, consider compliance reassessment vs. malabsorption workup.

MONITORING: TSH + Free T4 in 6 weeks, CBC and ferritin in 8 weeks.""",

    # William Nakamura — Amlodipine
    """CARE PLAN — William Nakamura | MRN-005 | Amlodipine 10mg QD

ASSESSMENT: 65-year-old male with uncontrolled HTN (avg 162/98) on dual therapy. Adding CCB (Amlodipine) as third agent per JNC guidelines. PAD and microalbuminuria increase urgency of BP control.

PLAN:
1. Add Amlodipine 10mg PO QD. Continue Lisinopril 20mg and HCTZ 25mg.
2. BP target: <130/80 (ADA goal given DM and microalbuminuria).
3. Low-sodium diet (<1.5g/day) counseling — dietitian referral.
4. Monitor for dependent edema (Amlodipine side effect) — elevate legs, review if significant.
5. Repeat BMP in 2 weeks — monitor K+ and Cr (ACE inhibitor + diuretic combination).
6. Consider increasing Lisinopril to 40mg at next visit if BP still not at goal.
7. Nephrology referral for ACR 85 mg/g — early CKD management.

MONITORING: Home BP log BID, BMP in 2 weeks, ACR q6 months, cardiology follow-up.""",

    # William Nakamura — Atorvastatin
    """CARE PLAN — William Nakamura | MRN-005 | Atorvastatin 80mg (Intensification Discussion)

ASSESSMENT: Very-high-risk patient (PAD + DM) with LDL 72 mg/dL on maximum statin — LDL target is <55 mg/dL. Gap of 17 mg/dL requires additional lipid-lowering therapy.

PLAN:
1. Continue Atorvastatin 80mg QD — do not reduce.
2. Add Ezetimibe 10mg QD (next step per ACC/AHA algorithm) — expect additional 15–20% LDL reduction.
3. If LDL remains >55 after 3 months on statin + ezetimibe, discuss PCSK9 inhibitor (Evolocumab or Alirocumab) — prior authorization required.
4. TG 290 (elevated) — counsel on fish oil 4g/day or consider Icosapent ethyl (Vascepa) given high CV risk.
5. Continue Aspirin 81mg for PAD — do not discontinue.
6. Vascular surgery follow-up for ABI 0.78 — supervise exercise therapy for PAD.

MONITORING: Lipid panel in 6 weeks (post-ezetimibe), CK if myopathy symptoms, LFTs annually.""",
]


class Command(BaseCommand):
    help = "Seed database with mock patients, providers, orders, and care plans"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing data before seeding",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            CarePlan.objects.all().delete()
            Order.objects.all().delete()
            Patient.objects.all().delete()
            Provider.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared existing data."))

        providers = []
        for p in PROVIDERS:
            provider, created = Provider.objects.get_or_create(npi=p["npi"], defaults={"name": p["name"]})
            providers.append(provider)
            self.stdout.write(f"  Provider: {provider.name} (NPI {provider.npi})")

        patients = []
        for p in PATIENTS:
            patient, created = Patient.objects.get_or_create(
                mrn=p["mrn"],
                defaults={
                    "first_name": p["first_name"],
                    "last_name": p["last_name"],
                    "date_of_birth": p["date_of_birth"],
                },
            )
            patients.append(patient)
            self.stdout.write(f"  Patient: {patient.first_name} {patient.last_name} (MRN {patient.mrn})")

        for i, (patient_idx, provider_idx, order_data) in enumerate(ORDERS):
            patient = patients[patient_idx]
            provider = providers[provider_idx]
            order = Order.objects.create(
                patient=patient,
                provider=provider,
                **order_data,
            )
            care_plan = CarePlan.objects.create(
                order=order,
                content=CARE_PLAN_CONTENT[i],
                status="completed",
            )
            self.stdout.write(
                f"  Order + CarePlan: {patient.first_name} {patient.last_name} — {order.medication_name}"
            )

        self.stdout.write(self.style.SUCCESS(
            f"\nSeeded: {len(PATIENTS)} patients, {len(PROVIDERS)} providers, "
            f"{len(ORDERS)} orders, {len(ORDERS)} care plans."
        ))
