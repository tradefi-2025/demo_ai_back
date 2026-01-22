package org.trader.backdemo.entity;

import com.fasterxml.jackson.annotation.JsonBackReference;
import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;

import java.util.Set;

@Entity
@Getter
@Setter
@Table(name = "agent")

public class AgentEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "agent_id")
    private long id;

    @Column(name = "name")
    private String name;

    @Column(name = "target_market")
    private String targetMarket;

    @Column(name = "input_start_time")
    private String inputStartTime;

    @Column(name = "input_end_time")
    private String inputEndTime;

    @Enumerated(EnumType.STRING)
    @Column(name = "frequency")
    private Frequency frequency;

    @Column(name = "output_start_time")
    private String outputStartTime;

    @Column(name = "output_end_time")
    private String outputEndTime;

    @Enumerated(EnumType.STRING)
    @Column(name = "training_status")
    private Status trainingStatus = Status.PENDING;

    @Enumerated(EnumType.STRING)
    @Column(name = "prediction_scale")
    private PredictionScale predictionScale;

    @Column(name = "version")
    private String version;

    @ManyToOne
    @JoinColumn(name = "user_id")
    @JsonBackReference
    private UserEntity user;

    @OneToMany(mappedBy = "agent", cascade = CascadeType.ALL, orphanRemoval = true)
    private Set<AgentFeatureEntity> agentFeatures;

    public enum Status {
        PENDING,
        IN_PROGRESS,
        COMPLETED,
        FAILED,
        CANCELLED
    }

    public enum Frequency {
        MIN_1,
        MIN_5,
        MIN_15,
        MIN_30,
        HOUR_1,
        DAY_1,
        WEEK_1
    }

    public enum PredictionScale {
        HOURLY,
        DAILY,
        WEEKLY,
        MONTHLY
    }

}
