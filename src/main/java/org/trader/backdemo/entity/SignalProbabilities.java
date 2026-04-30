package org.trader.backdemo.entity;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class SignalProbabilities {
    private Double sell;
    private Double hold;
    private Double buy;
}
