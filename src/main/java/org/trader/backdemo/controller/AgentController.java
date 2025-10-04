package org.trader.backdemo.controller;

import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;
import org.trader.backdemo.dto.request.AgentFormRequest;
import org.trader.backdemo.service.AgentService;

@RequiredArgsConstructor
@RestController
@RequestMapping("/api/agent")
public class AgentController {

    private final AgentService agentService;

    @PostMapping("/create")
    public ResponseEntity<Boolean> createAgent(@RequestBody AgentFormRequest agentFormRequest,
                                               @AuthenticationPrincipal(expression = "id") Long userId) {
        return agentService.createAgent(agentFormRequest, userId);
    }

    @GetMapping("/findByUserId")
    public ResponseEntity<?> agentsByUserId(@AuthenticationPrincipal(expression = "id") Long userId) {
        return agentService.agentsByUserId(userId);
    }
}