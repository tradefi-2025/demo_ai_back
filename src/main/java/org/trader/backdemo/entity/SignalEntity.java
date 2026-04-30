package org.trader.backdemo.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.LocalDateTime;

@Entity
@Getter
@Setter
@Table(name = "signal")
public class SignalEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "signal_id")
    private long id;

    @Column(name = "signal_date")
    private LocalDateTime signalDate;

    @Column(name = "estimated_action")
    private String estimatedAction;

    @Column(name = "signal")
    private String signal;

    @Column(name = "probability")
    private Double probability;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "probabilities", columnDefinition = "jsonb")
    private SignalProbabilities probabilities;

    @Column(name = "volume")
    private Double volume;

    @Column(name = "notional")
    private Double notional;

    @Column(name = "stop_loss_price")
    private Double stopLossPrice;

    @Column(name = "risk_amount")
    private Double riskAmount;

    @Column(name = "sizing_method")
    private String sizingMethod;

    @JdbcTypeCode(SqlTypes.ARRAY)
    @Column(name = "warnings", columnDefinition = "text[]")
    private String[] warnings;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false)
    private SignalStatus status = SignalStatus.NEW;

    @ManyToOne
    @JoinColumn(name = "agent_id", nullable = false)
    @JsonIgnore
    private AgentEntity agent;

    public enum SignalStatus {
        NEW,
        READ,
        ARCHIVED
    }
}
