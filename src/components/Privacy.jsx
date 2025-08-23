import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import './Privacy.css';
import logoPng from '../assets/fxsentinel_logo_nobg.png';
import logoWebp from '../assets/fxsentinel_logo_nobg.webp';

const Privacy = () => {
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      const scrollPosition = window.scrollY;
      setIsScrolled(scrollPosition > 50);
    };

    window.addEventListener('scroll', handleScroll);
    
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  };

  return (
    <div className="privacy-page">
      {/* Navigation */}
      <nav className={`navbar ${isScrolled ? 'navbar-scrolled' : ''}`}>
        <div className="nav-container">
          <div className="nav-logo" onClick={scrollToTop} style={{ cursor: 'pointer' }}>
            <picture>
              <source srcSet={logoWebp} type="image/webp" />
              <img 
                src={logoPng} 
                alt="FXSentinel Logo" 
                className="logo"
                style={{ height: '50px', width: 'auto' }}
              />
            </picture>
          </div>
          
          {/* Desktop Navigation Links */}
          <div className="nav-links desktop-only">
            <Link to="/" className="nav-link-button">Home</Link>
            <Link to="/dashboard" className="nav-link-button">Dashboard</Link>
          </div>
          
          {/* Desktop Auth Buttons */}
          <div className="nav-auth desktop-only">
            <Link to="/login" className="login-button">Login</Link>
            <Link to="/signup" className="signup-button">Sign Up</Link>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="privacy-content">
        <div className="privacy-inner">
          <h1 className="privacy-title">Privacy Policy</h1>
          
          <div className="privacy-section">
            <h2>Introduction</h2>
            <p>
              At FXSentinel, we are committed to protecting your privacy and ensuring the security 
              of your personal information. This Privacy Policy explains how we collect, use, 
              disclose, and safeguard your information when you use our platform and services.
            </p>
            <p>
              By using FXSentinel, you consent to the data practices described in this policy. 
              If you do not agree with our policies and practices, please do not use our services.
            </p>
          </div>

          <div className="privacy-section">
            <h2>Information We Collect</h2>
            
            <h3>Personal Information</h3>
            <p>
              We may collect personal information that you provide directly to us, including:
            </p>
            <ul>
              <li>Name and email address when you create an account</li>
              <li>Payment information when you subscribe to our services</li>
              <li>Communication preferences and settings</li>
              <li>Feedback and correspondence with our support team</li>
            </ul>

            <h3>Usage Information</h3>
            <p>
              We automatically collect certain information about your use of our platform:
            </p>
            <ul>
              <li>IP address and device information</li>
              <li>Browser type and version</li>
              <li>Pages visited and features used</li>
              <li>Time spent on different sections of the platform</li>
              <li>Error logs and performance data</li>
            </ul>

            <h3>Market Data</h3>
            <p>
              We collect and process market data from various financial sources to provide our 
              analysis services. This data does not contain personal information and is used 
              solely for market analysis and insights.
            </p>
          </div>

          <div className="privacy-section">
            <h2>How We Use Your Information</h2>
            <p>We use the information we collect for the following purposes:</p>
            <ul>
              <li>To provide and maintain our services</li>
              <li>To process payments and manage subscriptions</li>
              <li>To send you important updates and notifications</li>
              <li>To improve our platform and develop new features</li>
              <li>To provide customer support and respond to inquiries</li>
              <li>To ensure the security and integrity of our platform</li>
              <li>To comply with legal obligations</li>
            </ul>
          </div>

          <div className="privacy-section">
            <h2>Information Sharing and Disclosure</h2>
            <p>
              We do not sell, trade, or otherwise transfer your personal information to third 
              parties without your consent, except in the following circumstances:
            </p>
            
            <h3>Service Providers</h3>
            <p>
              We may share your information with trusted third-party service providers who 
              assist us in operating our platform, such as:
            </p>
            <ul>
              <li>Payment processors for subscription management</li>
              <li>Cloud hosting providers for data storage</li>
              <li>Analytics services to improve our platform</li>
              <li>Customer support tools</li>
            </ul>

            <h3>Legal Requirements</h3>
            <p>
              We may disclose your information if required by law or in response to valid 
              legal requests, such as subpoenas or court orders.
            </p>

            <h3>Business Transfers</h3>
            <p>
              In the event of a merger, acquisition, or sale of assets, your information 
              may be transferred as part of the business transaction.
            </p>
          </div>

          <div className="privacy-section">
            <h2>Data Security</h2>
            <p>
              We implement appropriate technical and organizational measures to protect your 
              personal information against unauthorized access, alteration, disclosure, or 
              destruction. These measures include:
            </p>
            <ul>
              <li>Encryption of data in transit and at rest</li>
              <li>Regular security assessments and updates</li>
              <li>Access controls and authentication measures</li>
              <li>Secure data centers and infrastructure</li>
              <li>Employee training on data protection</li>
            </ul>
            <p>
              However, no method of transmission over the internet or electronic storage is 
              100% secure, and we cannot guarantee absolute security.
            </p>
          </div>

          <div className="privacy-section">
            <h2>Data Retention</h2>
            <p>
              We retain your personal information for as long as necessary to provide our 
              services and fulfill the purposes outlined in this policy. When you cancel 
              your account, we will delete or anonymize your personal information within 
              30 days, except where we are required to retain certain information for 
              legal or regulatory purposes.
            </p>
          </div>

          <div className="privacy-section">
            <h2>Your Rights and Choices</h2>
            <p>You have the following rights regarding your personal information:</p>
            
            <h3>Access and Correction</h3>
            <p>
              You can access and update your personal information through your account 
              settings or by contacting us directly.
            </p>

            <h3>Data Portability</h3>
            <p>
              You can request a copy of your personal information in a structured, 
              machine-readable format.
            </p>

            <h3>Deletion</h3>
            <p>
              You can request deletion of your personal information, subject to certain 
              legal and contractual obligations.
            </p>

            <h3>Marketing Communications</h3>
            <p>
              You can opt out of marketing communications by following the unsubscribe 
              instructions in our emails or by contacting us.
            </p>
          </div>

          <div className="privacy-section">
            <h2>Cookies and Tracking Technologies</h2>
            <p>
              We use cookies and similar tracking technologies to enhance your experience 
              on our platform. These technologies help us:
            </p>
            <ul>
              <li>Remember your preferences and settings</li>
              <li>Analyze platform usage and performance</li>
              <li>Provide personalized content and features</li>
              <li>Ensure platform security and functionality</li>
            </ul>
            <p>
              You can control cookie settings through your browser preferences, though 
              disabling certain cookies may affect platform functionality.
            </p>
          </div>

          <div className="privacy-section">
            <h2>International Data Transfers</h2>
            <p>
              Your information may be transferred to and processed in countries other than 
              your own. We ensure that such transfers comply with applicable data protection 
              laws and implement appropriate safeguards to protect your information.
            </p>
          </div>

          <div className="privacy-section">
            <h2>Children's Privacy</h2>
            <p>
              Our services are not intended for children under the age of 18. We do not 
              knowingly collect personal information from children under 18. If you believe 
              we have collected information from a child under 18, please contact us 
              immediately.
            </p>
          </div>

          <div className="privacy-section">
            <h2>Changes to This Policy</h2>
            <p>
              We may update this Privacy Policy from time to time to reflect changes in 
              our practices or applicable laws. We will notify you of any material changes 
              by posting the updated policy on our platform and updating the "Last Updated" 
              date.
            </p>
          </div>

          <div className="privacy-section">
            <h2>Contact Us</h2>
            <p>
              If you have any questions about this Privacy Policy or our data practices, 
              please contact us at 
              <a href="mailto:fxsentinelapp@gmail.com" className="contact-link"> fxsentinelapp@gmail.com</a>
            </p>
          </div>

          <div className="privacy-footer">
            <p><strong>Last updated:</strong> August 2025</p>
            <p>
              By using FXSentinel, you acknowledge that you have read and understood this 
              Privacy Policy and consent to the collection, use, and disclosure of your 
              information as described herein.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Privacy;
