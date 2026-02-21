# Invoice Annotations Reference

Invoice annotations are required metadata fields that indicate special tax treatment or procedures. For most standard invoices, all annotations should be set to their "NO" or "REGULAR" values.

## InvoiceAnnotations

Container for all required annotation fields.

```python
from ksef.models.invoice_annotations import (
    InvoiceAnnotations,
    TaxSettlementOnPayment,
    SelfInvoicing,
    ReverseCharge,
    SplitPayment,
    FreeFromVat,
    IntraCommunitySupplyOfNewTransportMethods,
    SimplifiedProcedureBySecondTaxPayer,
    MarginProcedure,
)

# Standard invoice - all defaults
annotations = InvoiceAnnotations(
    tax_settlement_on_payment=TaxSettlementOnPayment.REGULAR,
    self_invoice=SelfInvoicing.NO,
    reverse_charge=ReverseCharge.NO,
    split_payment=SplitPayment.NO,
    free_from_vat=FreeFromVat.NO,
    intra_community_supply_of_new_transport_methods=IntraCommunitySupplyOfNewTransportMethods.NO,
    simplified_procedure_by_second_tax_payer=SimplifiedProcedureBySecondTaxPayer.NO,
    margin_procedure=MarginProcedure.NO,
)
```

---

## Annotation Fields

### TaxSettlementOnPayment (P_16)

Cash accounting method (metoda kasowa).

| Value | Description |
|-------|-------------|
| `REGULAR` | Standard tax settlement |
| `ON_PAYMENT` | Tax settled on payment receipt |

```python
from ksef.models.invoice_annotations import TaxSettlementOnPayment

# Standard - tax on invoice date
TaxSettlementOnPayment.REGULAR

# Cash method - tax on payment date
TaxSettlementOnPayment.ON_PAYMENT
```

---

### SelfInvoicing (P_17)

Self-invoicing (samofakturowanie) - when buyer issues invoice on behalf of seller.

| Value | Description |
|-------|-------------|
| `NO` | Normal invoice issued by seller |
| `YES` | Self-invoice issued by buyer |

```python
from ksef.models.invoice_annotations import SelfInvoicing

SelfInvoicing.NO   # Normal invoice
SelfInvoicing.YES  # Self-invoice
```

---

### ReverseCharge (P_18)

Reverse charge mechanism (odwrotne obciążenie) - buyer pays VAT instead of seller.

| Value | Description |
|-------|-------------|
| `NO` | Normal VAT treatment |
| `YES` | Reverse charge applies |

```python
from ksef.models.invoice_annotations import ReverseCharge

ReverseCharge.NO   # Normal
ReverseCharge.YES  # Reverse charge
```

---

### SplitPayment (P_18A)

Split payment mechanism (mechanizm podzielonej płatności) - mandatory for certain transactions over 15,000 PLN.

| Value | Description |
|-------|-------------|
| `NO` | Normal payment |
| `YES` | Split payment required |

```python
from ksef.models.invoice_annotations import SplitPayment

SplitPayment.NO   # Normal
SplitPayment.YES  # Split payment
```

---

### FreeFromVat (P_19)

VAT exemption (zwolnienie z VAT).

| Value | Description |
|-------|-------------|
| `NO` | Normal VAT applies |
| `YES` | VAT exempt |

```python
from ksef.models.invoice_annotations import FreeFromVat

FreeFromVat.NO   # Normal VAT
FreeFromVat.YES  # VAT exempt
```

---

### IntraCommunitySupplyOfNewTransportMethods (P_22)

Intra-community supply of new means of transport (wewnątrzwspólnotowa dostawa nowych środków transportu).

| Value | Description |
|-------|-------------|
| `NO` | Not applicable |
| `YES` | Intra-community supply of new transport |

```python
from ksef.models.invoice_annotations import IntraCommunitySupplyOfNewTransportMethods

IntraCommunitySupplyOfNewTransportMethods.NO
IntraCommunitySupplyOfNewTransportMethods.YES
```

---

### SimplifiedProcedureBySecondTaxPayer (P_23)

Simplified procedure in triangular transactions by second taxpayer.

| Value | Description |
|-------|-------------|
| `NO` | Not applicable |
| `YES` | Simplified triangular procedure |

```python
from ksef.models.invoice_annotations import SimplifiedProcedureBySecondTaxPayer

SimplifiedProcedureBySecondTaxPayer.NO
SimplifiedProcedureBySecondTaxPayer.YES
```

---

### MarginProcedure (P_PMarzy)

Margin scheme procedure (procedura marży) - for second-hand goods, art, antiques.

| Value | Description |
|-------|-------------|
| `NO` | Normal procedure |
| `YES` | Margin scheme applies |

```python
from ksef.models.invoice_annotations import MarginProcedure

MarginProcedure.NO   # Normal
MarginProcedure.YES  # Margin scheme
```

---

## Common Scenarios

### Standard Invoice

For most B2B invoices:

```python
annotations = InvoiceAnnotations(
    tax_settlement_on_payment=TaxSettlementOnPayment.REGULAR,
    self_invoice=SelfInvoicing.NO,
    reverse_charge=ReverseCharge.NO,
    split_payment=SplitPayment.NO,
    free_from_vat=FreeFromVat.NO,
    intra_community_supply_of_new_transport_methods=IntraCommunitySupplyOfNewTransportMethods.NO,
    simplified_procedure_by_second_tax_payer=SimplifiedProcedureBySecondTaxPayer.NO,
    margin_procedure=MarginProcedure.NO,
)
```

### Split Payment Required

For transactions over 15,000 PLN with certain goods/services:

```python
annotations = InvoiceAnnotations(
    tax_settlement_on_payment=TaxSettlementOnPayment.REGULAR,
    self_invoice=SelfInvoicing.NO,
    reverse_charge=ReverseCharge.NO,
    split_payment=SplitPayment.YES,  # Split payment required
    free_from_vat=FreeFromVat.NO,
    intra_community_supply_of_new_transport_methods=IntraCommunitySupplyOfNewTransportMethods.NO,
    simplified_procedure_by_second_tax_payer=SimplifiedProcedureBySecondTaxPayer.NO,
    margin_procedure=MarginProcedure.NO,
)
```

### VAT Exempt

For VAT-exempt transactions:

```python
annotations = InvoiceAnnotations(
    tax_settlement_on_payment=TaxSettlementOnPayment.REGULAR,
    self_invoice=SelfInvoicing.NO,
    reverse_charge=ReverseCharge.NO,
    split_payment=SplitPayment.NO,
    free_from_vat=FreeFromVat.YES,  # VAT exempt
    intra_community_supply_of_new_transport_methods=IntraCommunitySupplyOfNewTransportMethods.NO,
    simplified_procedure_by_second_tax_payer=SimplifiedProcedureBySecondTaxPayer.NO,
    margin_procedure=MarginProcedure.NO,
)
```
