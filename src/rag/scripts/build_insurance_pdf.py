import os
from rag.config import DEFAULT_DOCUMENT_PATH
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

PDF_OUTPUT_PATH = str(DEFAULT_DOCUMENT_PATH)

PAGES_DATA = [
    # Page 1
    """SBI General Insurance Company Limited
PRIVATE CAR INSURANCE POLICY - PACKAGE
POLICY WORDING

1. DEFINITIONS
1. Accident means sudden, unforeseen, and involuntary event caused by external, visible, and violent means.
2. Act means the Insurance Act, 1938 (4 of 1938).
3. Authority means the Insurance Regulatory and Development Authority of India established under the provisions of section 3 of the Insurance Regulatory and Development Authority Act, 1999 (41 of 1999).
4. Competent Authority means (i) Chairperson, or (ii) such whole-time member or such committee of the whole-time members or such officer(s) of the Authority, as may be determined by the Chairperson.
5. Complaint / Grievance means written expression (includes communication in the form of electronic mail or voice based electronic scripts) of dissatisfaction by a complainant with respect to solicitation or sale or purchase of an insurance policy or related services by insurer and /or by distribution channel.
6. Complainant means a policyholder or prospect or nominee or assignee or any beneficiary of an insurance policy who has filed a complaint or grievance against an insurer and /or distribution channel.
7. Cover means an insurance contract whether in the form of a policy document or a Certificate of Insurance or any other form as may be specified to evidence the existence of an insurance contract.
8. Distribution Channels include insurance agents, intermediaries or insurance intermediaries, and any persons or entities authorised by the Authority to involve in sale and service of insurance policies.
9. Proposal form means a form to be filled in by the prospect in physical or electronic form, for furnishing the information including material information, if any, as required by the insurer in respect of a risk, in order to enable the insurer to take informed decision in the context of underwriting the risk, and in the event of acceptance of the risk, to determine the rates, advantages, terms and conditions of the cover to be granted.
10. Policy Period means the period commencing with the Commencement Date of the Policy and terminating with the expiry of the Policy as stated in the Policy Schedule/Schedule.
11. Policy Schedule/Schedule means the Schedule attached to and forming part of this Policy specifying the details of the Insured Vehicle, the Sum Insured, the Policy Period and the Sub-limits to which benefits under the Policy are subject to, including any annexures and/or endorsements, made to or on it from time to time, and if more than one, then the latest in time.
12. Prospect means any person who is a potential customer and likely to enter into an insurance contract either directly with the insurer or through the distribution channel involved.
13. Prospectus means a document either in physical or electronic format issued by the insurer to sell or promote the insurance product.
14. Solicitation means the act of approaching a prospect or a customer by an insurer or by a distribution channel with a view to persuading the prospect or a policyholder to purchase or to renew an insurance policy.
15. Unfair trade practice shall have the meaning ascribed to such term in the Consumer Protection Act, 2019, as amended from time to time.
16. Salvage The value of a vehicle that has met with an accident and has been damaged to such an extent that it no longer makes economic sense to repair.

2. COVERAGE
Whereas the Insured by a proposal and declaration dated as stated in the Schedule which shall be the basis of this contract and is deemed to be incorporated herein has applied to SBI GENERAL INSURANCE COMPANY LIMITED (hereinafter called "the Company") for the insurance hereinafter contained and has paid the premium mentioned in the Schedule as consideration for such insurance in respect of accidental loss or damage occurring during the period of insurance.

NOW THIS POLICY WITNESSETH:
That subject to the Terms Exceptions and Conditions contained herein or endorsed or expressed hereon;
a) SECTION I - LOSS OF OR DAMAGE TO THE VEHICLE INSURED
1. The Company will indemnify the Insured against loss or damage to the vehicle insured hereunder and / or its accessories whilst thereon
i. by fire explosion self ignition or lightning ;
ii. by burglary housebreaking or theft ;
iii. by riot and strike;
iv. by earthquake (fire and shock damage);
v. by flood typhoon hurricane storm tempest inundation cyclone hailstorm frost;
vi. by accidental external means;
vii. by malicious act;
viii. by terrorist activity; ix. whilst in transit by road rail inland-waterway lift elevator or air;
x. by landslide rockslide.

Subject to a deduction for depreciation at the rates mentioned below in respect of parts replaced:
(1) For all rubber/ nylon / plastic parts, tyres and tubes, batteries and air bags - 50%
(2) For fibre glass components - 30%
(3) For all parts made of glass - Nil
(4) Rate of depreciation for all other parts including wooden parts will be as per the following schedule:
- Not exceeding 6 months: NIL
- Exceeding 6 months but not exceeding 1 year: 5%
- Exceeding 1 year but not exceeding 2 years: 10%
- Exceeding 2 years but not exceeding 3 years: 15%
- Exceeding 3 years but not exceeding 4 years: 25%
- Exceeding 4 years but not exceeding 5 years: 35%
- Exceeding 5 years but not exceeding 10 years: 40%
- Exceeding 10 years: 50%""",

    # Page 2
    """SBI General Insurance Company Limited
PRIVATE CAR INSURANCE POLICY - PACKAGE

2. The Company shall not be liable to make any payment in respect of:
(a) consequential loss, depreciation, wear and tear, mechanical or electrical breakdown, failures or breakages
(b) damage to Tyres and Tubes unless the vehicle is damaged at the same time in which case the liability of the Company shall be limited to 50% of the cost of replacement.
(c) any accidental loss or damage suffered whilst the Insured or any person driving the vehicle with the knowledge and consent of the Insured is under the influence of intoxicating liquor or drugs.

3. In the event of the vehicle being disabled by reason of loss or damage covered under this Policy, the Company will bear the reasonable cost of protection and removal to the nearest repairer and re-delivery to the Insured but not exceeding in all, Rs 1500/- in respect of any one accident.

4. The Insured may authorise the repair of the vehicle necessitated by damage for which the Company may be liable under this Policy provided that:
(a) the estimated cost of such repair including replacements, if any, does not exceed Rs 500/-;
(b) the Company is furnished forthwith with a detailed estimate of the cost of repairs; and
(c) the Insured shall give the Company every assistance to see that such repair is necessary and the charges are reasonable.

b) SECTION II - LIABILITY TO THIRD PARTIES
1. Subject to the limits of liability as laid down in the Schedule hereto the Company will indemnify the Insured in the event of an accident caused by or arising out of the use of the vehicle against all sums which the Insured shall become legally liable to pay in respect of :-
i) death of or bodily injury to any person including occupants carried in the vehicle (provided such occupants are not carried for hire or reward) but except so far as it is necessary to meet the requirements of Motor Vehicles Act, the Company shall not be liable where such death or injury arises out of and in course of employment of such person by the Insured.
ii) damage to property other than property belonging to the Insured or held in trust or in the custody or control of the Insured.
2. The Company will pay all costs and expenses incurred with its written consent.
3. In terms of and subject to the limitations of the indemnity granted by this Section to the Insured, the Company will indemnify any driver who is driving the vehicle on the Insured's order or with Insured's permission provided that such driver shall as though he/she was the Insured observe fulfill and be subject to the terms exceptions and conditions of this Policy in so far as they apply.
4. In the event of the death of any person entitled to indemnity under this Policy the Company will in respect of the liability incurred by such person indemnify his/her personal representative in terms of and subject to the limitations of this Policy.
5. The Company may at its own option (a) arrange for representation at any Inquest or Fatal Inquiry and (b) undertake the defence of proceedings in any Court of Law.

c) SECTION III - PERSONAL ACCIDENT COVER FOR OWNER-DRIVER
The Company undertakes to pay compensation as per the following scale for bodily injury/ death sustained by the owner-driver of the vehicle in direct connection with the vehicle insured or whilst driving or whilst mounting into/dismounting from the insured vehicle or whilst traveling in it as a co-driver, caused by violent accidental external and visible means which independent of any other cause shall within six calendar months of such injury result in:
- (i) Death: 100% Scale of compensation
- (ii) Loss of two limbs or sight of two eyes or one limb and sight of one eye: 100%
- (iii) Loss of one limb or sight of one eye: 50%
- (iv) Permanent total disablement from injuries other than named above: 100%

Provided Always that:
A. Compensation shall be payable under only one of the items (i) to (iv) above in respect of the owner-driver arising out of any one occurrence and the total liability of the Company shall not in the aggregate exceed the sum of Rs 15 lakhs during any one period of insurance.
B. No compensation shall be payable in respect of death or bodily injury directly or indirectly wholly or in part arising or resulting from intentional self injury, suicide or attempted suicide or an accident happening whilst under the influence of intoxicating liquor or drugs.

3. SUM INSURED - INSURED'S DECLARED VALUE (IDV)
The Insured's Declared Value (IDV) of the vehicle will be deemed to be the 'SUM INSURED' for the purpose of this Policy which is fixed at the commencement of each Policy period for the insured vehicle.
The IDV of the vehicle (and accessories if any fitted to the vehicle) is to be fixed on the basis of the manufacturer's listed selling price of the brand and model as the vehicle insured at the commencement of insurance/renewal and adjusted for depreciation.""",

    # Page 3
    """SBI General Insurance Company Limited
PRIVATE CAR INSURANCE POLICY - PACKAGE

THE SCHEDULE OF DEPRECIATION FOR FIXING IDV OF THE VEHICLE
- Not exceeding 6 months: 5%
- Exceeding 6 months but not exceeding 1 year: 15%
- Exceeding 1 year but not exceeding 2 years: 20%
- Exceeding 2 years but not exceeding 3 years: 30%
- Exceeding 3 years but not exceeding 4 years: 40%
- Exceeding 4 years but not exceeding 5 years: 50%

IDV of vehicles beyond 5 years of age and of obsolete models is to be determined on the basis of an understanding between the Company and the Insured.
IDV shall be treated as the 'Market Value' throughout the policy period without any further depreciation for the purpose of Total Loss (TL) / Constructive Total Loss (CTL) claims.
The insured vehicle shall be treated as a CTL if the aggregate cost of retrieval and / or repair of the vehicle exceeds 75% of the IDV of the vehicle.

4. AVOIDANCE OF CERTAIN TERMS AND RIGHT OF RECOVERY
Nothing in this Policy or any endorsement hereon shall affect the right of any person indemnified by this Policy or any other person to recover an amount under or by virtue of the provisions of the Motor Vehicles Act, 1988. But the Insured shall repay to the Company all sums paid by the Company which the Company would not have been liable to pay but for the said provisions.

5. APPLICATION OF LIMITS OF INDEMNITY
In the event of any accident involving indemnity to more than one person, any limitation by the terms of this Policy of the amount of any indemnity shall apply to the aggregate amount of indemnity to all persons indemnified and such indemnity shall apply in priority to the Insured.

6. GENERAL EXCEPTIONS (Applicable to all Sections of the Policy)
The Company shall not be liable under this Policy in respect of:
1. Any accidental loss or damage and/or liability caused sustained or incurred outside the geographical area;
2. Any claim arising out of any contractual liability;
3. Any accidental loss damage and/or liability caused sustained or incurred whilst the vehicle insured herein is:
   (a) being used otherwise than in accordance with the 'Limitations as to Use' or
   (b) being driven by or is for the purpose of being driven by him/her in the charge of any person other than a Driver as stated in the Driver's Clause.
4. (a) Any accidental loss or damage to any property whatsoever or any loss or expense whatsoever resulting or arising there from or any consequential loss.
   (b) Any liability of whatsoever nature directly or indirectly caused by or contributed to by or arising from ionising radiations or contamination by radioactivity from any nuclear fuel or from any nuclear waste.
5. Any accidental loss or damage or liability directly or indirectly caused by or contributed to by or arising from nuclear weapons material.
6. War, invasion, act of foreign enemies, hostilities or warlike operations, civil war, mutiny, rebellion, revolution, insurrection, military or usurped power.

7. DEDUCTIBLE
The Company shall not be liable for each and every claim under Section - I (loss of or damage to the vehicle insured) of this Policy in respect of the deductible stated in the Schedule.

8. CONDITIONS
1. Notice shall be given in writing to the Company immediately upon the occurrence of any accidental loss or damage. In case of theft or criminal act, immediate notice to police is mandatory.
2. No admission offer promise payment or indemnity shall be made or given by or on behalf of the Insured without the written consent of the Company.
3. The Company may at its own option repair reinstate or replace the vehicle or part thereof and/or its accessories or may pay in cash the amount of the loss or damage.""",

    # Page 4
    """SBI General Insurance Company Limited
PRIVATE CAR INSURANCE POLICY - PACKAGE

CONDITIONS (Continued)
(b) For partial losses, i.e. losses other than Total Loss/Constructive Total Loss of the vehicle - actual and reasonable costs of repair and/or replacement of parts lost/damaged subject to depreciation as per limits specified.
4. Safeguarding Vehicle: The Insured shall take all reasonable steps to safeguard the vehicle from loss or damage and to maintain it in efficient condition.
5. Cancellation:
- The insured can cancel the policy at any time during the term, by informing the company. The company can cancel the policy only on the grounds of established fraud, by giving minimum notice of 7 days to the retail policyholder.
- Under no circumstances can the company cancel statutory Motor Third Party Liability insurance, except in case of double insurance or total loss.
- The Company shall refund proportion premium for unexpired policy period if term is up to one year and no claim has been made.
- Where ownership of insured vehicle is transferred, policy cannot be cancelled unless evidence of insurance elsewhere is produced.
6. Contribution: If other insurance covers the same liability, Company pays ratable proportion.
7. Due observance of terms and truth of statements in proposal are conditions precedent to liability.
8. Death of Insured: Policy remains valid for 3 months from date of death or until expiry (whichever earlier) allowing legal heirs to apply for transfer.

9. ENDORSEMENTS
IMT.1. EXTENSION OF GEOGRAPHICAL AREA
Extension to include Nepal, Sri Lanka, Maldives, Bhutan, Pakistan, Bangladesh. Excludes sea voyage / air transit damage.

IMT.2. AGREED VALUE CLAUSE (Applicable only to Vintage Car)
In case of TOTAL LOSS/CONSTRUCTIVE TOTAL LOSS of Vintage Car, amount payable will be IDV without depreciation deduction.

IMT.3. TRANSFER OF INTEREST
Transfer of policy to new owner. No Claim Bonus earned by previous insured does not transfer.

IMT.4. CHANGE OF VEHICLE
Vehicle details deleted and replacement vehicle details included in schedule with premium adjustment.""",

    # Page 5
    """SBI General Insurance Company Limited
PRIVATE CAR INSURANCE POLICY - PACKAGE

ENDORSEMENTS (Continued)
IMT.5. HIRE PURCHASE AGREEMENT
Vehicle is subject of Hire Purchase Agreement. Loss/damage claims payable to Owners/Financier. Personal accident cover for owner-driver remains with named insured.

IMT.6. LEASE AGREEMENT
Vehicle is subject of Lease Agreement. Monies payable to Lessors. Named insured remains principal party.

IMT.7. VEHICLES SUBJECT TO HYPOTHECATION AGREEMENT
Vehicle is pledged/hypothecated to Pledgee/Bank. Monies payable to Pledgee as full discharge.

IMT.8. DISCOUNT FOR MEMBERSHIP OF RECOGNISED AUTOMOBILE ASSOCIATIONS
Discount allowed in consideration of membership of recognised Automobile Association.

IMT.9. DISCOUNT FOR VINTAGE CARS
Discount in premium allowed for vehicles certified as Vintage Car by Vintage and Classic Car Club of India.

IMT.10. INSTALLATION OF ANTI-THEFT DEVICE
Premium discount allowed for Anti-Theft device approved by Automobile Research Association of India (ARAI), Pune installed in vehicle.""",

    # Page 6
    """SBI General Insurance Company Limited
PRIVATE CAR INSURANCE POLICY - PACKAGE

ENDORSEMENTS (Continued)
IMT.11.A. VEHICLES LAID UP (Lay up period declared)
Vehicle is laid up in garage and not in use. Liability suspended except for accidental loss/damage by Fire, Explosion, Self-Ignition, Lightning, Burglary, Theft, Riot, Strike, Malicious Damage, Terrorism, Flood, Earthquake perils.

IMT.11.B. VEHICLES LAID UP (Lay up period not declared)
Liability suspended during undeclared lay up period save for specified perils.

IMT.11(C). TERMINATION OF THE UNDECLARED PERIOD OF VEHICLE LAID UP
Reinstatement of policy after lay up with premium credit/extension.

IMT.12. DISCOUNT FOR SPECIALLY DESIGNED/MODIFIED VEHICLES FOR THE BLIND, HANDICAPPED AND MENTALLY CHALLENGED PERSONS
Discount of 50% on Own Damage premium for specially designed/modified vehicles endorsed in Registration Book.

IMT.13. USE OF VEHICLE WITHIN INSURED'S OWN PREMISES
Covers use of vehicle confined to Insured's own premises (except for fighting fire).

IMT.15. PERSONAL ACCIDENT COVER TO THE INSURED OR ANY NAMED PERSON OTHER THAN PAID DRIVER OR CLEANER
Personal accident cover for bodily injury/death sustained in connection with vehicle or while mounting/dismounting.""",

    # Page 7
    """SBI General Insurance Company Limited
PRIVATE CAR INSURANCE POLICY - PACKAGE

PERSONAL ACCIDENT COMPENSATION SCALE:
- i) Death: 100%
- ii) Loss of two limbs or sight of two eyes or one limb and sight of one eye: 100%
- iii) Loss of one limb or sight of one eye: 50%
- iv) Permanent Total Disablement from injuries other than named above: 100%

IMT.16. PERSONAL ACCIDENT TO UNNAMED PASSENGERS OTHER THAN INSURED AND THE PAID DRIVER OR CLEANER
Covers unnamed passengers up to registered seating capacity of vehicle against accidental bodily injury or death within 3 months of occurrence.

IMT.17. PERSONAL ACCIDENT COVER TO PAID DRIVERS, CLEANERS AND CONDUCTORS
Covers paid driver, cleaner, or conductor in employ of Insured for bodily injury/death within 6 calendar months.

IMT.19. COVER FOR VEHICLES IMPORTED WITHOUT CUSTOMS DUTY
In event of loss/damage to imported vehicle requiring parts not obtainable in India, liability limited to catalogue price plus transport by sea and relative import duty.""",

    # Page 8
    """SBI General Insurance Company Limited
PRIVATE CAR INSURANCE POLICY - PACKAGE

ENDORSEMENTS (Continued)
IMT.20. REDUCTION IN THE LIMIT OF LIABILITY FOR PROPERTY DAMAGE
Liability for third party property damage limited to Rs 6,000/- (Rupees six thousand only) with corresponding premium reduction.

IMT.22. COMPULSORY DEDUCTIBLE
Insured bears specified compulsory deductible for each and every event under Section 1.

IMT.22A. VOLUNTARY DEDUCTIBLE
Additional voluntary deductible opted by insured in exchange for premium reduction under Section 1.

IMT.24. ELECTRICAL / ELECTRONIC FITTINGS
Covers loss or damage to declared electrical/electronic fittings not included in manufacturer's listed selling price. Excludes mechanical/electrical breakdown.

IMT.25. CNG / LPG KIT IN BI-FUEL SYSTEM (Own Damage cover for the kit)
Covers accidental loss/damage to CNG/LPG kit fitted in vehicle subject to declared IDV of the kit.

IMT.26. FIRE AND/OR THEFT RISKS ONLY
Restricts policy to Fire and/or Theft risks only under Section I; Section II liability is cancelled.""",

    # Page 9
    """SBI General Insurance Company Limited
PRIVATE CAR INSURANCE POLICY - PACKAGE

ENDORSEMENTS (Continued)
IMT.27. LIABILITY AND FIRE AND / OR THEFT
Covers third party liability plus loss/damage by fire and/or theft.

IMT.28. LEGAL LIABILITY TO PAID DRIVER AND/OR CONDUCTOR AND/OR CLEANER EMPLOYED IN CONNECTION WITH THE OPERATION OF INSURED VEHICLE
Indemnifies legal liability under Workmen's Compensation Act, 1923, Fatal Accidents Act, 1855 or Common Law for premium of Rs 50/- per employee.

IMT.29. LEGAL LIABILITY TO EMPLOYEES OF THE INSURED OTHER THAN PAID DRIVER WHO MAY BE TRAVELLING OR DRIVING IN THE EMPLOYER'S CAR
Premium of Rs 50/- per employee for statutory and common law liability.

IMT.30. TRAILERS
Extends indemnity to attached Trailer (specified Registration Number and IDV).

IMT.31. RELIABILITY TRIALS AND RALLIES
Extends policy coverage while participating in approved reliability trials/rallies (excludes organized racing or speed testing).""",

    # Page 10
    """SBI General Insurance Company Limited
PRIVATE CAR INSURANCE POLICY - PACKAGE

IMT.32. ACCIDENTS TO SOLDIERS / SAILORS / AIRMEN EMPLOYED AS DRIVERS
Additional premium of Rs 100/- relieves Insured of liability to indemnify Ministry of Defence.

10. CLAIM SETTLEMENT
The Company will settle claims within 7 days of receipt of surveyor report and necessary documents (Driving License, FIR, fitness certificate, permit, claim form). Rejection decisions communicated within 22 days of Survey Report.

11. GRIEVANCE REDRESSAL PROCEDURE
- Stage 1: Bima Bharosa (IRDAI Portal): https://bimabharosa.irdai.gov.in/
- Stage 2: Head - Customer Care (Email: head.customercare@sbigeneral.in | Toll-Free: 1800 102 1111 | Senior Citizens: Seniorcitizengrivences@sbigeneral.in)
- Stage 3: Grievance Redressal Officer (GRO) - Virag Mishra, Phone: 022-45138021, Email: gro@sbigeneral.in. Resolution TAT: 14 days.
- Stage 4: Escalation to Insurance Ombudsman (https://www.cioins.co.in/Ombudsman)

ANNEXURE I - INSURANCE OMBUDSMAN CENTRES (Part 1)
- Gujarat, Dadra & Nagar Haveli, Daman & Diu: Ahmedabad (Shri Collu Vikas Rao) Tel: 079-25501201
- Karnataka: Bengaluru (Mr Vipin Anand) Tel: 080-26652048
- Madhya Pradesh, Chhattisgarh: Bhopal (Shri R. M. Singh) Tel: 0755-2769201
- Odisha: Bhubaneswar (Shri Manoj Kumar Parida) Tel: 0674-2596461
- Punjab, Haryana, HP, J&K, Ladakh, Chandigarh: Chandigarh (Mr Atul Jerath) Tel: 0172-4646394""",

    # Page 11
    """SBI General Insurance Company Limited
PRIVATE CAR INSURANCE POLICY - PACKAGE

ANNEXURE I - INSURANCE OMBUDSMAN CENTRES (Part 2)
- Tamil Nadu, Puducherry: Chennai (Shri Somnath Ghosh) Tel: 044-24333668
- Delhi & Haryana districts: New Delhi (Ms Sunita Sharma) Tel: 011-23232481
- Assam, Meghalaya, Manipur, Mizoram, Arunachal Pradesh, Nagaland, Tripura: Guwahati (Shri Somnath Ghosh) Tel: 0361-2632204
- Andhra Pradesh, Telangana, Yanam: Hyderabad (Shri N. Sankaran) Tel: 040-23312122
- Rajasthan: Jaipur (Shri Rajiv Dutt Sharma) Tel: 0141-2740363
- Kerala, Lakshadweep, Mahe: Ernakulam (Shri G. Radhakrishnan) Tel: 0484-2358759
- West Bengal, Sikkim, Andaman & Nicobar: Kolkata (Ms Kiran Sahdev) Tel: 033-22124339
- UP (Lucknow, Kanpur, Varanasi, etc.): Lucknow (Shri Atul Sahai) Tel: 0522-2231330
- Goa, Mumbai Metropolitan Region: Mumbai (Ms Susmita Mukherjee) Tel: 022-69038800
- Uttarakhand & Western UP (Noida, Agra, Meerut): Noida (Shri Bimbadhar Pradhan) Tel: 0120-2514252
- Bihar, Jharkhand: Patna (Ms Susmita Mukherjee) Tel: 0612-2547068
- Maharashtra (Pune, Navi Mumbai, Thane): Pune (Shri Sunil Jain) Tel: 020-41312555""",

    # Page 12
    """SBI General Insurance Company Limited
PRIVATE CAR INSURANCE POLICY - PACKAGE

12. ADD ONS (ANNEXURE III)
1. DEPRECIATION REIMBURSEMENT (Zero Depreciation)
Reimburses the amount of depreciation deducted on replaced parts for approved partial loss claims under Section I.
Exclusions: Total Loss / Constructive Total Loss / Theft claims; parts not approved by Company; repair costs exceeding insured value.

2. PROTECTION OF NCB (No Claim Bonus)
Retains existing NCB tier at renewal even if one claim is lodged during the policy period, provided vehicle is renewed with SBI General and repaired at Authorized Garage.

3. COVER FOR CONSUMABLES
Covers expenses incurred for consumable items: nuts, bolts, screws, washers, grease, lubricants, gearbox oil, AC gas, bearings, distilled water, engine oil, oil filter, fuel filter, and brake oil.

4. ENGINE GUARD
Covers damage to internal child parts of engine and gearbox arising from: (1) Water ingression (hydrostatic lock), (2) Leakage of lubricating oil due to accidental external damage.
Includes pistons, connecting rods, crankshaft, cylinder head, gears, shafts.

5. BASIC ROAD-SIDE ASSISTANCE
Towing assistance (mechanical & electrical breakdown) up to nearest garage. Custody and storage of vehicle, delivery of spare parts within 72 hours.""",

    # Page 13
    """SBI General Insurance Company Limited
PRIVATE CAR INSURANCE POLICY - PACKAGE

ADD ONS (Continued) - BASIC ROAD-SIDE ASSISTANCE (Cont.)
2. Towing Assistance (Accident): Free towing to nearest Authorized Garage up to covered distance.
3. Flat Tyre: On-spot assistance to replace flat tyre with spare tyre.
4. Dead Battery: Jump-start assistance to mobilize vehicle.
5. Keys Locked-In: Retrieval of duplicate keys from insured's address or authorized lock-opening service.
6. Fuel Assistance: Delivery of up to 10 litres of emergency fuel (Petrol/Diesel) when stranded >=1 km from petrol station.

General Exclusions to Road-Side Assistance:
- Confiscation / detention by legal authorities.
- Natural catastrophes (flood, tempest, earthquake, tsunami) where accessibility is cut off.
- War, strikes, civil commotion, riot.""",

    # Page 14
    """SBI General Insurance Company Limited
PRIVATE CAR INSURANCE POLICY - PACKAGE

6. ADDITIONAL ROAD-SIDE ASSISTANCE
1. Continuation of Journey: Taxi/hired car for occupants to continue journey or return home (up to 2 times per policy period).
2. Local Travel when on Tour: Alternate hired car for local travel while car is under repair (>100 km from home) for up to 3 days (8 hrs/80 km per day).
3. Overnight Accommodation Expense when on Tour: Hotel accommodation on twin sharing basis up to Rs 2,500/- per person per night (max Rs 25,000/- per event, up to 3 days) if repairs exceed 3 days.
4. Repatriation of Vehicle: Repatriation of repaired vehicle to home address if repairs take >72 hours (>100 km from home).
5. Medical Co-ordination: Ambulance service coordination and medical conference call assistance (ambulance cost covered up to Rs 2,500).""",

    # Page 15
    """SBI General Insurance Company Limited
PRIVATE CAR INSURANCE POLICY - PACKAGE

ADD ONS (Continued)
6. Urgent Message Relay: Urgent message transmission to family when immobilized >100 km away.

7. LOSS OF PERSONAL BELONGINGS
Covers loss or damage to personal belongings (clothes, laptop, mobile, jewellery) inside vehicle during accident or burglary. Max payout: Rs 50,000/- per year. Deductibles: Rs 5,000 for Laptop/Jewellery, Rs 2,500 for Mobiles, Rs 500 for others.

8. COVER FOR KEY REPLACEMENTS
Reimburses replacement of lost, stolen keys or broken lock sets up to Rs 65,000/- per policy year at Authorized Garage (10% co-share, min Rs 500).

9. RETURN TO INVOICE
In case of Total Loss, CTL or Theft, pays difference between IDV and original purchase invoice price (or current replacement price), plus reimbursement of first-time road tax and registration fees.

10. BATTERY GUARD
Covers repair/replacement of EV battery, ISG, ECM, CPU, Inverter, Charger Port, Onboard Charger due to power surge during charging or water ingression/short circuit.""",

    # Page 16
    """SBI General Insurance Company Limited
PRIVATE CAR INSURANCE POLICY - PACKAGE

ADD ONS (Continued)
10. Battery Guard Exclusions:
Ageing, wear and tear, charging not as per OEM guidelines, already dead battery, EV uncharged for >24 hrs after deep discharge, unauthorized repair/alteration.

11. GO SMART - FLEXI COVER (Pay As You Drive / Kilometer Based)
Coverage limited to opted kilometer slab (e.g. 5,000 km, 10,000 km).
- Top-up option available if kilometers are exceeded.
- Grace limit of up to 100 km.
- Up to 1,000 unused km can be carried forward on renewal.
- Odometer tampering results in policy forfeiture.

12. ENHANCED PERSONAL ACCIDENT COVER FOR THE INSURED (OWNER DRIVER)
Enhanced capital sum insured and expanded schedule of bodily injury coverage.""",

    # Page 17
    """SBI General Insurance Company Limited
PRIVATE CAR INSURANCE POLICY - PACKAGE

ENHANCED PERSONAL ACCIDENT COMPENSATION SCALES:
- i) Death: 100%
- ii) Loss of two limbs or sight of two eyes or one limb and sight of one eye: 100%
- iii) Loss of one limb or sight of one eye: 50%
- iv) Permanent Total Disablement: 100%
- v) Speech and hearing in Both ears: 100%
- vi) Speech OR Hearing in Both ears: 50%
- vii) Hearing in One ear: 25%
- viii) Thumb and index finger of same hand: 25%
- ix) Loss of Toes - All: 20%
- x) Great Toe: 5%
- xi) Other than Great Toe: 1% each
- xii) Loss of four fingers and thumb of one hand: 40%
- xiii) Loss of Four fingers except thumb: 25%
- xiv) Loss of thumb: 5%
- xv) Loss of index finger: 10%
- xvi) Loss of middle finger: 6%
- xvii) Loss of ring finger: 5%
- xviii) Loss of little finger: 4%

13. ENHANCED PERSONAL ACCIDENT COVER FOR PAID DRIVER OF THE VEHICLE
Applies compensation scale to employed paid drivers.

14. ENHANCED PERSONAL ACCIDENT COVER FOR UN-NAMED PASSENGERS OF THE VEHICLE
Applies compensation scale to unnamed vehicle occupants/passengers.""",

    # Page 18
    """SBI General Insurance Company Limited
PRIVATE CAR INSURANCE POLICY - PACKAGE

ADD ONS (Continued)
15. INCONVENIENCE ALLOWANCE
Daily cash benefit during vehicle repair following admissible Own Damage claim (max 10 days, after 3-day deductible) at Authorized Garage. Applicable for first 2 claims per policy period.

16. WALL CHARGER AND ASSOCIATED ACCESSORIES (Electric Vehicles)
Covers permanent EV wall charger, charging unit, adapter, cable installed at insured's communication address against fire, theft, malicious damage, rodent bites, power fluctuations, impact of foreign bodies, external impact.
Exclusions: Manufacturer defect, unauthorized installation, battery malfunction, wear & tear.""",

    # Page 19
    """SBI General Insurance Company Limited
PRIVATE CAR INSURANCE POLICY - PACKAGE

ADD ONS (Continued)
17. VEHICLE REPLACEMENT EDGE
In Total Loss / CTL / Theft, provides replacement with new vehicle of same make/model/variant (or last published ex-showroom price if discontinued), excluding registration/taxes.

18. EMERGENCY MEDICAL EXPENSES
Emergency medical treatment expenses for occupants injured in accident up to Sum Insured. Includes ambulance charges up to Rs 2,500/-. Treatment must commence within 5 days of accident.

19. EMI PROTECTOR
Pays Equated Monthly Installment (EMI) payable to Financial Institution for up to 2 months if vehicle repair time exceeds 21 days due to covered peril under Section I.""",

    # Page 20
    """SBI General Insurance Company Limited
PRIVATE CAR INSURANCE POLICY - PACKAGE

20. TYRE AND RIM SECURE
a. Tyre Replacement:
- Unused tread depth >7mm: 100% cost of new tyre/tube
- Unused tread depth >=5 to <7mm: 75% cost
- Unused tread depth >=3 to <5mm: 50% cost
- Unused tread depth <3mm: Excluded (normal wear and tear)
b. Rim Cover:
Covers accidental damage/warping to rims from potholes, kerbs, road debris. Max 4 replacements per policy period.

Specific Exclusions: Non-authorized garage repairs, non-OEM rims/tyres, corrosion/rust, minor scratches, racing/rallying.""",

    # Page 21
    """SBI General Insurance Company Limited
PRIVATE CAR INSURANCE POLICY - PACKAGE

ADD ONS (Continued)
21. PROFESSIONAL FEES FOR APP RESTORATION COVER
Reimburses technician fees at Authorized OEM store after cyber incident / malware infection to clean, decontaminate, restore and reconfigure manufacturer vehicle software on personal device. Excludes software upgrade costs and data misuse.

NOTE TO ADD ON COVERS
Policy Year means 12 consecutive months starting from Policy commencement date and ending on expiry date as specified in Schedule.

SBI General Insurance Company Limited, Corporate & Registered Office: Fulcrum Building, 9th Floor, A & B Wing, Sahar Road, Andheri (East), Mumbai - 400099.
IRDAI Reg No: 144 | UIN: IRDAN144RP0005V03201112"""
]

def generate_pdf():
    os.makedirs(os.path.dirname(PDF_OUTPUT_PATH), exist_ok=True)
    c = canvas.Canvas(PDF_OUTPUT_PATH, pagesize=letter)
    width, height = letter
    
    for page_num, page_text in enumerate(PAGES_DATA, start=1):
        # Draw header banner
        c.setFillColor(colors.HexColor("#0f2b5c"))
        c.rect(0, height - 40, width, 40, fill=True, stroke=False)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(36, height - 25, "SBI General Insurance Company Limited — Policy Wording")
        
        c.setFont("Helvetica", 9)
        c.drawRightString(width - 36, height - 25, f"Page {page_num} of {len(PAGES_DATA)}")
        
        # Draw body text
        text_obj = c.beginText(36, height - 60)
        text_obj.setFont("Helvetica", 9)
        text_obj.setFillColor(colors.HexColor("#1a1a1a"))
        text_obj.setLeading(12)
        
        lines = page_text.split("\n")
        for line in lines:
            if not line.strip():
                text_obj.textLine("")
                continue
            
            # Simple bold styling for headings
            if line.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "10.", "11.", "12.", "13.", "14.", "15.", "16.", "17.", "18.", "19.", "20.", "21.", "IMT.", "SECTION", "ANNEXURE", "NOW THIS", "THE SCHEDULE")):
                text_obj.setFont("Helvetica-Bold", 9.5)
                text_obj.setFillColor(colors.HexColor("#0f2b5c"))
            elif line.startswith(("-", "•", "i)", "ii)", "iii)", "iv)", "v)", "vi)", "vii)", "viii)", "ix)", "x)")):
                text_obj.setFont("Helvetica", 8.5)
                text_obj.setFillColor(colors.HexColor("#2d3748"))
            else:
                text_obj.setFont("Helvetica", 8.5)
                text_obj.setFillColor(colors.HexColor("#1a1a1a"))
                
            # Wrap long line
            words = line.split(" ")
            current_line = ""
            for word in words:
                if len(current_line) + len(word) + 1 > 95:
                    text_obj.textLine(current_line)
                    current_line = word
                else:
                    current_line = f"{current_line} {word}".strip()
            if current_line:
                text_obj.textLine(current_line)
                
        c.drawText(text_obj)
        
        # Draw footer
        c.setStrokeColor(colors.HexColor("#cbd5e0"))
        c.setLineWidth(0.5)
        c.line(36, 35, width - 36, 35)
        c.setFont("Helvetica", 7.5)
        c.setFillColor(colors.HexColor("#718096"))
        c.drawString(36, 22, "Private Car Insurance Policy - Package | UIN: IRDAN144RP0005V03201112 | IRDAI Reg No: 144")
        c.drawRightString(width - 36, 22, f"SBI General Insurance — Page {page_num}")
        
        c.showPage()
        
    c.save()
    print(f"Generated {len(PAGES_DATA)} pages PDF at: {PDF_OUTPUT_PATH}")

if __name__ == "__main__":
    generate_pdf()
