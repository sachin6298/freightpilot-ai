import { Page, IconName } from '../types';
import Icon from './Icon';

const PAGE_LABELS: Record<Page, string> = {
  overview: 'Overview',
  shipments: 'Shipments',
  quotes: 'Freight Quotes',
  risk: 'Risk Manager',
  copilot: 'AI Copilot',
  payments: 'Payments',
  analytics: 'Analytics',
  carriers: 'Carriers',
  documents: 'Documents',
  settings: 'Settings',
  landing: 'Home',
};

const PAGE_ICONS: Record<Page, IconName> = {
  overview: 'overview',
  shipments: 'shipments',
  quotes: 'quotes',
  risk: 'risk',
  copilot: 'copilot',
  payments: 'payments',
  analytics: 'analytics',
  carriers: 'truck',
  documents: 'file',
  settings: 'settings',
  landing: 'overview',
};

interface BreadcrumbsProps {
  currentPage: Page;
  activeShipmentId?: string;
  onNavigate?: (page: Page) => void;
  onBack?: () => void;
}

export default function Breadcrumbs({ currentPage, activeShipmentId, onNavigate, onBack }: BreadcrumbsProps) {
  const handleBack = () => {
    if (onBack) {
      onBack();
    } else if (window.history.length > 1) {
      window.history.back();
    } else {
      onNavigate?.('overview');
    }
  };

  return (
    <nav className="breadcrumbs" aria-label="Breadcrumb navigation">
      {currentPage !== 'overview' && (
        <button
          className="breadcrumbs-back-btn"
          onClick={handleBack}
          aria-label="Go back"
          title="Return to previous screen"
        >
          <Icon name="arrow" size={14} />
          <span>Back</span>
        </button>
      )}

      <ol className="breadcrumbs-list">
        <li className="breadcrumbs-item">
          <button
            className="breadcrumbs-link"
            onClick={() => onNavigate?.('overview')}
            aria-label="Workspace Overview"
          >
            <Icon name="overview" size={13} />
            <span>Overview</span>
          </button>
        </li>

        {currentPage !== 'overview' && (
          <li className="breadcrumbs-item">
            <span className="breadcrumbs-separator" aria-hidden="true">
              <Icon name="chevron" size={11} />
            </span>
            {!activeShipmentId ? (
              <span className="breadcrumbs-current" aria-current="page">
                <Icon name={PAGE_ICONS[currentPage]} size={13} />
                <span>{PAGE_LABELS[currentPage]}</span>
              </span>
            ) : (
              <button
                className="breadcrumbs-link"
                onClick={() => onNavigate?.(currentPage)}
                aria-label={`Go to ${PAGE_LABELS[currentPage]}`}
              >
                <Icon name={PAGE_ICONS[currentPage]} size={13} />
                <span>{PAGE_LABELS[currentPage]}</span>
              </button>
            )}
          </li>
        )}

        {activeShipmentId && (
          <li className="breadcrumbs-item">
            <span className="breadcrumbs-separator" aria-hidden="true">
              <Icon name="chevron" size={11} />
            </span>
            <span className="breadcrumbs-current mono" aria-current="page">
              <Icon name="shipments" size={13} />
              <span>{activeShipmentId}</span>
            </span>
          </li>
        )}
      </ol>
    </nav>
  );
}