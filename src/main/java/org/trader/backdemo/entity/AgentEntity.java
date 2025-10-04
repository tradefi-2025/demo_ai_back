package org.trader.backdemo.entity;

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

    @Column(name = "input_frequency")
    private int inputFrequency;

    @Column(name = "output_start_time")
    private String outputStartTime;

    @Column(name = "output_end_time")
    private String outputEndTime;

    @Column(name = "output_frequency")
    private int outputFrequency;

    @Enumerated(EnumType.STRING)
    @Column(name = "training_status")
    private Status trainingStatus = Status.PENDING;

    @ManyToOne
    @JoinColumn(name = "user_id")
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

}
