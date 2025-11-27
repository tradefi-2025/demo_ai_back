package org.trader.backdemo.controller;


import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.trader.backdemo.dto.request.UserInscriptionRequest;
import org.trader.backdemo.dto.request.UserLoginRequest;
import org.trader.backdemo.service.AuthService;
import org.trader.backdemo.service.UserService;

@RequiredArgsConstructor
@RequestMapping("/api/auth")
@RestController
public class AuthController {

    private final UserService userService;
    private final AuthService authService;

    @PostMapping("/inscription")
    public ResponseEntity<String> inscription(@RequestBody UserInscriptionRequest userInscriptionRequest) {
        return userService.inscription(userInscriptionRequest);
    }

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody UserLoginRequest userLoginRequest) {
        return authService.signIn(userLoginRequest);
    }


    @PostMapping("logout")
    public ResponseEntity<?> logOut() {
        return authService.logOutUser();
    }
}
