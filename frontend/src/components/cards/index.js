// Component registry — keyed by ui_block "type".
// To add a new card: create MyCard.jsx, import it below, add one entry.
import ProductCard from "./ProductCard";
import CompatibilityBadge from "./CompatibilityBadge";
import InstallSteps from "./InstallSteps";
import OrderCard from "./OrderCard";
import CartConfirmation from "./CartConfirmation";
import TroubleshootResult from "./TroubleshootResult";

const CARD_REGISTRY = {
  product_card: ProductCard,
  compatibility_result: CompatibilityBadge,
  install_guide: InstallSteps,
  order_card: OrderCard,
  cart_confirmation: CartConfirmation,
  troubleshoot_result: TroubleshootResult,
};

export default CARD_REGISTRY;
