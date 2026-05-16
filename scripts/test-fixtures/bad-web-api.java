// Fixture: triggers pack-web-api rules.
package com.example;

import org.springframework.web.bind.annotation.*;
import org.springframework.beans.factory.annotation.Autowired;

@RestController
public class UserController {

    @Autowired
    private UserService service;

    private static final String API_BASE = "https://api.production.example.net/v1";

    @PostMapping("/users")
    public User create(@RequestBody UserDto dto) {  // missing @Valid
        try {
            return service.create(dto);
        } catch (Exception e) {  // broad catch + swallow
            e.printStackTrace();  // print stack trace
            return null;
        }
    }
}
