import React, { useState } from 'react';
import { AnimatePresence, LayoutGroup, motion, type Transition } from 'motion/react';
import { Fingerprint, X } from 'lucide-react';

export interface FamilyReceiveComponentProps {
  triggerLabel?: string;
  title?: string;
  description?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm?: () => void;
  icon?: React.ReactNode;
}

const springTransition: Transition = { type: 'spring', bounce: 0, duration: 0.4 };

export const FamilyReceiveComponent: React.FC<FamilyReceiveComponentProps> = ({
  triggerLabel = 'Continue',
  title = 'Confirm action',
  description = 'Continue with this action?',
  confirmLabel = 'Continue',
  cancelLabel = 'Cancel',
  onConfirm,
  icon,
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const confirm = () => {
    onConfirm?.();
    setIsOpen(false);
  };

  return (
    <LayoutGroup>
      <AnimatePresence mode="wait">
        {!isOpen && (
          <motion.button
            key="trigger"
            layoutId="fp-confirm-action"
            type="button"
            onClick={() => setIsOpen(true)}
            className="fp-confirm-trigger"
            whileTap={{ scale: 0.96 }}
            transition={springTransition}
          >
            {triggerLabel}
          </motion.button>
        )}
      </AnimatePresence>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            className="fp-confirm-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onMouseDown={(event) => { if (event.target === event.currentTarget) setIsOpen(false); }}
          >
            <motion.section
              role="dialog"
              aria-modal="true"
              aria-labelledby="fp-confirm-title"
              className="fp-confirm-dialog"
              initial={{ y: 24, opacity: 0, scale: 0.97 }}
              animate={{ y: 0, opacity: 1, scale: 1 }}
              exit={{ y: 18, opacity: 0, scale: 0.98 }}
              transition={springTransition}
            >
              <button type="button" className="fp-confirm-close" aria-label="Close confirmation" onClick={() => setIsOpen(false)}><X size={19}/></button>
              <div className="fp-confirm-heading">
                <span className="fp-confirm-icon">{icon ?? <Fingerprint size={23}/>}</span>
                <h2 id="fp-confirm-title">{title}</h2>
              </div>
              <p>{description}</p>
              <div className="fp-confirm-actions">
                <button type="button" className="fp-confirm-cancel" onClick={() => setIsOpen(false)}>{cancelLabel}</button>
                <motion.button type="button" layoutId="fp-confirm-action" className="fp-confirm-accept" onClick={confirm} transition={springTransition}>{confirmLabel}</motion.button>
              </div>
            </motion.section>
          </motion.div>
        )}
      </AnimatePresence>
    </LayoutGroup>
  );
};
