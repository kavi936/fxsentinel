import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import './InfoIcon.css';

const InfoIcon = ({ tooltipText, position = 'top' }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [tooltipPosition, setTooltipPosition] = useState({ top: 0, left: 0 });
  const iconRef = useRef(null);

  useEffect(() => {
    if (isVisible && iconRef.current) {
      const rect = iconRef.current.getBoundingClientRect();
      const tooltipWidth = 380; // max-width from CSS
      const tooltipHeight = 100; // approximate height
      const spacing = 8;

      let top = 0;
      let left = 0;

      switch (position) {
        case 'bottom':
          top = rect.bottom + spacing;
          left = rect.left + (rect.width / 2);
          break;
        case 'top':
          top = rect.top - tooltipHeight - spacing;
          left = rect.left + (rect.width / 2);
          break;
        case 'left':
          top = rect.top + (rect.height / 2);
          left = rect.left - tooltipWidth - spacing;
          break;
        case 'right':
          top = rect.top + (rect.height / 2);
          left = rect.right + spacing;
          break;
        default:
          top = rect.bottom + spacing;
          left = rect.left + (rect.width / 2);
      }

      // Ensure tooltip stays within viewport
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;

      // Adjust horizontal position if tooltip would overflow
      if (left - tooltipWidth / 2 < 0) {
        left = tooltipWidth / 2 + 10;
      } else if (left + tooltipWidth / 2 > viewportWidth) {
        left = viewportWidth - tooltipWidth / 2 - 10;
      }

      // Adjust vertical position if tooltip would overflow
      if (top < 0) {
        top = rect.bottom + spacing;
      } else if (top + tooltipHeight > viewportHeight) {
        top = rect.top - tooltipHeight - spacing;
      }

      setTooltipPosition({ top, left });
    }
  }, [isVisible, position]);

  const tooltipTransform =
    position === 'left' || position === 'right'
      ? 'translateY(-50%)'
      : 'translateX(-50%)';

  return (
    <>
      <div 
        ref={iconRef}
        className="info-icon-container"
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
      >
        <div className="info-icon">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"></circle>
            <path d="M12 16v-4"></path>
            <path d="M12 8h.01"></path>
          </svg>
        </div>
      </div>
      {isVisible && createPortal(
        <div 
          className={`info-tooltip info-tooltip-${position}`}
          style={{
            top: `${tooltipPosition.top}px`,
            left: `${tooltipPosition.left}px`,
            transform: tooltipTransform,
            zIndex: 999999
          }}
        >
          <div className="tooltip-content">
            {tooltipText}
          </div>
          <div className="tooltip-arrow"></div>
        </div>,
        document.body
      )}
    </>
  );
};

export default InfoIcon;
