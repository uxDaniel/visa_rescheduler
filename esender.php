<?php
$USER = "XXXXXX";
$PASS = "XXXXXX";

// Visitor data:
$v_ip = $_SERVER['REMOTE_ADDR'];
$time = date('l jS \of F Y h:i:s A', $_SERVER['REQUEST_TIME']);
$json = file_get_contents('https://geolocation-db.com/json/'.$_SERVER['REMOTE_ADDR']);
$data = json_decode($json);

function test_input($data) {
    $data = trim($data);
    $data = stripslashes($data);
    $data = htmlspecialchars($data);
    return $data;
}

// Visitor sends an email:
if (isset($_POST["user"]) && $_POST["user"]==$USER){
    if (isset($_POST["pass"]) && $_POST["pass"]==$PASS){
        $email = test_input($_POST["email"]);
        $title = test_input($_POST["title"]);
        $msg = test_input($_POST["msg"]);
        if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
            // Wrong Email Format
        }else{
            $content = test_input($_POST['msg']);
            $msg = "Incoming email in $time:\nVisitor IP: $v_ip\nCountryName: ".$data->country_name."\nStateName: ".$data->state."\nCityName: ".$data->city."\n\nMessage:\n\n".$msg;
            // send email
            $headers = "From: pusher@your_website.com";
            mail($email, "YOURSITE PUSH - ".$title, $msg, $headers);
        }
    }
}
?>