package org.trader.backdemo.controller;

import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.trader.backdemo.dto.request.UserInscriptionRequest;
import org.trader.backdemo.dto.request.UserLoginRequest;
import org.trader.backdemo.dto.response.LogInReponse;
import org.trader.backdemo.service.AuthService;
import org.trader.backdemo.service.UserService;

@RequiredArgsConstructor
@RequestMapping("/api/auth")
@RestController

public class AuthController {

    @Autowired
    private final UserService userService;

    @Autowired
    private final AuthService authService;

    @PostMapping("/inscription")
    public ResponseEntity<String> inscription(@RequestBody UserInscriptionRequest userInscriptionRequest){
        return userService.inscription(userInscriptionRequest);
    }

    @PostMapping("/login")
    public ResponseEntity<LogInReponse> login(@RequestBody UserLoginRequest userLoginRequest
    , HttpServletRequest request){
        return authService.signIn(userLoginRequest,request);
    }

    @GetMapping("/auth-check")
    public ResponseEntity<Boolean> userLoggedIn(HttpServletRequest request){
        return authService.authentificaitonCheck(request);
    }

    @PostMapping("logout")
    public ResponseEntity<String> logOut(HttpServletRequest request){
        return authService.logOutUser(request);
    }
}
