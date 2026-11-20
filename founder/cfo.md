# Unit economics: آتیوار — WaaS فلزات گران‌بها (مدل حساب فعال)

> **همه اعداد به تومان‌اند؛ ابزار خروجی را با علامت `$` نشان می‌دهد.** منابع و فرض‌ها: `founder/cfo-sources.md`

Every number below comes from the input file. Nothing is looked up or guessed.

## One حساب-ماه

| line | per حساب-ماه |
| --- | ---: |
| Price | $14,000.00 |
| تسویه، میزبانی و KYC | -$1,200.00 |
| پشتیبانی و عملیات | -$900.00 |
| **Contribution** (what each حساب-ماه leaves to pay the fixed costs) | **$11,900.00** (85%) |

## The margin that matters

Fixed costs: $2,580,000,000 a month (تیم ۱۰ نفره + سایر OpEx (۳۱ میلیارد در سال ۱) $2,580,000,000).

- **Break-even: 7,227 حساب-ماهs a day.** Below that you lose money every month.
- **Profit margin at your plan** (20,000 a day): **54%** of every sale, after every cost.
- Capacity: 33333 a day.

## Year 1, month by month

| month | حساب-ماهs a day | revenue | profit | cumulative (after $50,000,000,000 startup) |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 1,000 | $420,000,000 | -$2,223,000,000 | -$52,223,000,000 |
| 2 | 1,000 | $420,000,000 | -$2,223,000,000 | -$54,446,000,000 |
| 3 | 1,000 | $420,000,000 | -$2,223,000,000 | -$56,669,000,000 |
| 4 | 8,333 | $3,499,860,000 | $394,881,000 | -$56,274,119,000 |
| 5 | 8,333 | $3,499,860,000 | $394,881,000 | -$55,879,238,000 |
| 6 | 8,333 | $3,499,860,000 | $394,881,000 | -$55,484,357,000 |
| 7 | 20,000 | $8,400,000,000 | $4,560,000,000 | -$50,924,357,000 |
| 8 | 20,000 | $8,400,000,000 | $4,560,000,000 | -$46,364,357,000 |
| 9 | 20,000 | $8,400,000,000 | $4,560,000,000 | -$41,804,357,000 |
| 10 | 26,667 | $11,200,140,000 | $6,940,119,000 | -$34,864,238,000 |
| 11 | 26,667 | $11,200,140,000 | $6,940,119,000 | -$27,924,119,000 |
| 12 | 26,667 | $11,200,140,000 | $6,940,119,000 | -$20,984,000,000 |

- **Year 1 operating profit: $29,016,000,000** on $70,560,000,000 of revenue.
- After the $50,000,000,000 startup spend: -$20,984,000,000.
- Startup money earned back: not within year 1.
- Cash you need before it pays for itself: **$56,669,000,000**.

## What if

| scenario | margin at plan | break-even a day | year 1 profit |
| --- | ---: | ---: | ---: |
| Base plan | 54% | 7,227 | $29,016,000,000 |
| Price -10% | 49% | 8,191 | $21,960,000,000 |
| Volume -20% | 47% | 7,227 | $17,020,800,000 |
| Unit costs +15% | 52% | 7,424 | $27,428,400,000 |

## Red flags

- The startup spend is not earned back within year 1.
