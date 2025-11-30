---
description: Frontend UI fixes for broken/inactive links and features
---

# Frontend UI Fixes - Task List

**Status**: In Progress  
**Priority**: High  
**Estimated Time**: 2-3 days

---

## 📋 Task Breakdown

### 🔴 **CRITICAL - Navigation & Core UX** (Priority 1)

#### Navigation Bar
- [ ] **NAV-1**: Fix Home link (make it navigate to top of page)
- [ ] **NAV-2**: Fix Brand logo link (make it navigate to home)
- [ ] **NAV-3**: Remove duplicate dashboard link
- [ ] **NAV-4**: Fix Sign In/Out button functionality

**Files**: `src/components/Navigation.tsx`

---

### 🟡 **HIGH - Hero & Main CTAs** (Priority 2)

#### Hero Section
- [ ] **HERO-1**: Connect Subscribe CTA to subscription flow
- [ ] **HERO-2**: Connect Watch Success Stories CTA to video/modal
- [ ] **HERO-3**: Update hero text to reflect AI-powered business automation
- [ ] **HERO-4**: Add background video (placeholder until real video sourced)

**Files**: `src/components/HeroSection.tsx`

---

### 🟡 **HIGH - Services & Strategy Session** (Priority 2)

#### Services Section
- [ ] **SVC-1**: Fix "Get Custom Strategy" CTA - scroll to top of Strategy Session page
- [ ] **SVC-2**: Connect Subscribe button to subscription flow

**Files**: `src/components/ServicesSection.tsx`

#### Ready To Scale Your Business Card
- [ ] **SCALE-1**: Fix "Get Free Strategy Session" CTA - scroll to top
- [ ] **SCALE-2**: Connect Subscribe button to subscription flow

**Files**: Component location TBD (likely in `HeroSection.tsx` or separate component)

#### Ready to Experience the Difference Card
- [ ] **EXP-1**: Fix both CTAs to go to top of Strategy Session page (not halfway down)

**Files**: Component location TBD

---

### 🟢 **MEDIUM - Testimonials & Trust** (Priority 3)

#### Testimonials Section
- [ ] **TEST-1**: Fix first card profile image loading issue

**Files**: `src/components/TestimonialsSection.tsx`

#### Certified & Recognized By Card
- [ ] **CERT-1**: Replace placeholder images with actual company logos

**Files**: `src/components/TrustSection.tsx`

---

### 🟢 **MEDIUM - CTAs & Forms** (Priority 3)

#### Ready to Join Our Success Stories Card
- [ ] **SUCCESS-1**: Connect all CTA buttons to appropriate actions

**Files**: Component location TBD

#### Still Have Questions Card
- [ ] **FAQ-1**: Fix first CTA (currently returns 404)
- [ ] **FAQ-2**: Connect second CTA
- [ ] **FAQ-3**: Connect third CTA

**Files**: `src/components/FAQSection.tsx`

---

### 🟢 **MEDIUM - ROI & Demo** (Priority 3)

#### Calculate Your Potential ROI Section
- [ ] **ROI-1**: Fix popup card CTA buttons (currently return 404)

**Files**: `src/components/ROICalculator.tsx`

#### See Our AI In Action Section
- [ ] **DEMO-1**: Complete redesign with working CTA buttons
- [ ] **DEMO-2**: Add live interactive demo card
- [ ] **DEMO-3**: Update text with relevant AI automation information

**Files**: `src/components/DemoPreview.tsx`

---

### 🟡 **HIGH - Payments & Pricing** (Priority 2)

#### Choose Your Plan Section
- [ ] **PRICE-1**: Connect "Get Started" buttons to Stripe checkout
- [ ] **PRICE-2**: Remove alert popup, implement real checkout flow

**Files**: `src/components/PricingSection.tsx`

#### Get Your Free Consultation Form
- [ ] **CONSULT-1**: Connect Subscribe button to Stripe checkout
- [ ] **CONSULT-2**: Remove alert popup, implement real checkout flow

**Files**: `src/components/ContactSection.tsx`

---

### 🔵 **LOW - About & Footer** (Priority 4)

#### About Us Section
- [ ] **ABOUT-1**: Connect Subscribe button to subscription flow

**Files**: `src/components/AboutSection.tsx`

---

### 🔴 **CRITICAL - Dashboard Enhancement** (Priority 1)

#### Dashboard UX Improvements
- [ ] **DASH-1**: Add more insights and metrics
- [ ] **DASH-2**: Add client management tools
- [ ] **DASH-3**: Improve data visualization
- [ ] **DASH-4**: Add quick actions panel
- [ ] **DASH-5**: Add recent activity feed

**Files**: `src/pages/Dashboard.tsx`, `src/components/DashboardLayout.tsx`

---

## 🎯 Implementation Strategy

### Phase 1: Navigation & Core Functionality (Day 1)
1. Fix Navigation bar (NAV-1 to NAV-4)
2. Fix Stripe payment integration (PRICE-1, PRICE-2, CONSULT-1, CONSULT-2)
3. Fix scroll-to-top issues (SVC-1, SCALE-1, EXP-1)

### Phase 2: Hero & CTAs (Day 1-2)
1. Update Hero section text and CTAs (HERO-1 to HERO-4)
2. Connect all Subscribe buttons (SVC-2, SCALE-2, ABOUT-1)
3. Fix FAQ CTAs (FAQ-1 to FAQ-3)

### Phase 3: Content & Media (Day 2)
1. Fix testimonial images (TEST-1)
2. Update company logos (CERT-1)
3. Add background video placeholder (HERO-4)

### Phase 4: ROI & Demo Redesign (Day 2-3)
1. Fix ROI calculator CTAs (ROI-1)
2. Redesign AI Demo section (DEMO-1 to DEMO-3)

### Phase 5: Dashboard Enhancement (Day 3)
1. Add new insights and tools (DASH-1 to DASH-5)

---

## 📊 Progress Tracking

**Total Tasks**: 38  
**Completed**: 0  
**In Progress**: 0  
**Blocked**: 0

### By Priority
- **Critical (P1)**: 9 tasks
- **High (P2)**: 10 tasks
- **Medium (P3)**: 13 tasks
- **Low (P4)**: 1 task

### By Category
- **Navigation**: 4 tasks
- **Hero**: 4 tasks
- **Services/CTAs**: 11 tasks
- **Testimonials/Trust**: 2 tasks
- **ROI/Demo**: 4 tasks
- **Payments**: 4 tasks
- **Dashboard**: 5 tasks
- **About/Footer**: 1 task

---

## 🔧 Technical Notes

### Stripe Integration
- Backend endpoint: `/api/payments/create-checkout-session`
- Success URL: `/payments/success`
- Cancel URL: `/payments/cancel`
- Ensure `STRIPE_API_KEY` is configured in `.env`

### Scroll to Top Fix
Use React Router's hash navigation or scroll behavior:
```tsx
import { useNavigate } from 'react-router-dom';

const navigate = useNavigate();
navigate('/strategy-session', { replace: true });
window.scrollTo({ top: 0, behavior: 'smooth' });
```

### Subscribe Button Pattern
All subscribe buttons should:
1. Check if user is authenticated
2. If yes, redirect to pricing/checkout
3. If no, redirect to auth page with return URL

---

## 📝 Testing Checklist

After each fix:
- [ ] Test on desktop (Chrome, Firefox, Safari)
- [ ] Test on mobile (responsive design)
- [ ] Verify navigation flow
- [ ] Check console for errors
- [ ] Test with/without authentication
- [ ] Verify Stripe integration in test mode

---

## 🚀 Deployment Notes

- Test all changes in development first
- Use feature flags for major redesigns (Demo section)
- Deploy in phases to minimize risk
- Monitor error rates in Sentry after deployment

---

**Last Updated**: 2025-11-30  
**Next Review**: After Phase 1 completion
