# Technical Architecture Logic

This document shows how the crypto technical structure layer converts K-line data into a single technical dimension vote.

## Crypto 4H Market Structure

```mermaid
flowchart TD
    A[Binance 4H K-lines] --> B[Normalize OHLCV rows]
    B --> C{Enough rows?}
    C -- No --> C1[Mark technical structure missing]
    C -- Yes --> D[Detect swing highs and swing lows]

    D --> E[Measure swing high slope]
    D --> F[Measure swing low slope]
    E --> G{Structure Type}
    F --> G

    G -- Higher highs + higher lows --> G1[Ascending channel]
    G -- Lower highs + lower lows --> G2[Descending channel]
    G -- Lower highs + higher lows --> G3[Converging triangle / wedge]
    G -- Higher highs + lower lows --> G4[Expanding range]
    G -- Flat and narrow --> G5[Range box]
    G -- Flat and wide --> G6[Wide range]

    G1 --> H[Project upper and lower rails]
    G2 --> H
    G3 --> H
    G4 --> H
    G5 --> H
    G6 --> H

    H --> I{Current price location}
    I -- Above upper rail + buffer --> I1[Breakout above rail]
    I -- Below lower rail + buffer --> I2[Breakdown below rail]
    I -- Inside rail, near upper --> I3[Inside, near upper rail]
    I -- Inside rail, middle --> I4[Inside, mid-channel]
    I -- Inside rail, near lower --> I5[Inside, near lower rail]

    I1 --> J1[Architecture stance: bullish]
    I2 --> J2[Architecture stance: bearish]
    I3 --> J3[Architecture stance depends on structure]
    I4 --> J4[Architecture stance: neutral unless channel confirms]
    I5 --> J5[Architecture stance depends on structure]
```

## Technical Dimension Vote

```mermaid
flowchart TD
    A[Daily + 4H K-lines] --> B[Price bias]
    A --> C[4H dominant behavior]
    A --> D[4H market architecture]

    B --> E{Bias}
    E -- Daily up + higher 4H low --> E1[Technical proxy bullish]
    E -- Daily down + lower 4H high --> E2[Technical proxy bearish]
    E -- Mixed --> E3[Technical proxy neutral]

    C --> F{Behavior}
    F -- Trend advance --> F1[Behavior bullish]
    F -- Distribution / grinding down --> F2[Behavior bearish]
    F -- Box / failed breakdown recovery --> F3[Behavior neutral]

    D --> G{Architecture stance}
    G -- Bullish --> G1[Architecture bullish]
    G -- Bearish --> G2[Architecture bearish]
    G -- Neutral --> G3[Architecture neutral]

    E1 --> H[Collapse into one technical dimension]
    E2 --> H
    E3 --> H
    F1 --> H
    F2 --> H
    F3 --> H
    G1 --> H
    G2 --> H
    G3 --> H

    H --> I{Internal conflict?}
    I -- Only bullish proxies --> I1[Technical dimension = bullish]
    I -- Only bearish proxies --> I2[Technical dimension = bearish]
    I -- Bullish and bearish proxies --> I3[Technical dimension = neutral conflict]
    I -- Only neutral proxies --> I4[Technical dimension = neutral]

    I1 --> J[Seven-dimension gate]
    I2 --> J
    I3 --> J
    I4 --> J
```

## Decision Boundary

The market architecture layer is a technical proxy only. It can influence the technical structure dimension, but it cannot override contracts, macro, sentiment, exchange validation, news, options, or the CZSC confirmation layer.

For example:

- `Ascending channel + price inside upper half` can support the technical dimension.
- `Descending channel + price near upper rail` is not automatically bullish; it is usually a resistance test unless price breaks and holds above the rail.
- `Breakout above upper rail` is bullish only as a technical proxy; it still needs the direction quality gate to pass.
- `Expanding range` usually means unstable structure and should tend neutral unless a clean breakout or breakdown is confirmed.
