package org.trader.backdemo.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.trader.backdemo.dto.request.AgentFormRequest;
import org.trader.backdemo.service.AgentService;

@RestController
@RequestMapping("/api/agent")
public class AgentController {

    @Autowired
    private AgentService agentService ;

    @PostMapping("/create")
    public ResponseEntity<Boolean> createAgent(@RequestBody AgentFormRequest agentFormRequest ) {
        return agentService.createAgent(agentFormRequest);
    }



}
