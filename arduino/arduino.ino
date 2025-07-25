#include <Servo.h>

// Définir les servomoteurs
Servo servo1;
Servo servo2;
Servo servo3;
Servo servo4;
Servo servo5;
Servo servo6;

// Variables pour stocker les coordonnées reçues
int x_position = 0;
int y_position = 0;
float length = 0.0;
String inputString = "";  // Variable pour stocker les données série

void setup() {
  // Attacher les servomoteurs aux broches correspondantes
  servo1.attach(2);
  servo2.attach(3);
  servo3.attach(4);
  servo4.attach(5);
  servo5.attach(6);
  servo6.attach(7);

  // Initialiser la communication série
  Serial.begin(9600);

  // Initialisation du bras à une position de départ
  initialize_arm();
}

void loop() {
  // Lire les données série si disponibles
  if (Serial.available() > 0) {
    inputString = Serial.readStringUntil('\n');

    // Extraire les informations X, Y, Length et Angle
    if (inputString.startsWith("X:")) {
      int x_start = inputString.indexOf(':') + 1;
      int y_start = inputString.indexOf('Y:') + 2;
      int length_start = inputString.indexOf("Length:") + 7;
      int angle_start = inputString.indexOf("Angle:") + 6;

      x_position = inputString.substring(x_start, inputString.indexOf(',')).toInt();
      y_position = inputString.substring(y_start, inputString.indexOf(',', y_start)).toInt();
      length = inputString.substring(length_start, inputString.indexOf(',', length_start) > 0 ? inputString.indexOf(',', length_start) : inputString.length()).toFloat();
      float angle = 0.0;
      if (inputString.indexOf("Angle:") > 0) {
        angle = inputString.substring(angle_start).toFloat();
      }

      // Afficher les valeurs reçues pour vérification
      Serial.print("X Position: ");
      Serial.println(x_position);
      Serial.print("Y Position: ");
      Serial.println(y_position);
      Serial.print("Longueur: ");
      Serial.println(length);
      Serial.print("Angle: ");
      Serial.println(angle);

      // Déplacer le bras vers la position et l'orientation du tuyau
      move_arm_to_position(x_position, y_position, angle);
      
      // Saisir le tuyau si la longueur est supérieure à une certaine valeur
      if (length > 50.0) {
        grab_pipe();
        Serial.println("STATUS:OK");
      } else {
        Serial.println("Tuyau trop petit pour être saisi.");
        Serial.println("STATUS:FAIL");
      }
    }
  }
}

// Fonction pour initialiser la position du bras
void initialize_arm() {
  servo1.write(90);  // Position de départ
  servo2.write(90);
  servo3.write(90);
  servo4.write(90);
  servo5.write(90);
  servo6.write(90);
  delay(1000);
}

// Fonction pour déplacer le bras en fonction des coordonnées et de l'orientation du tuyau
void move_arm_to_position(int x, int y, float angle) {
  // Mappage x et y aux angles des servos, à ajuster selon votre configuration mécanique.
  int angle1 = map(x, 0, 640, 0, 180);  // Mappage x aux angles du servo1
  int angle2 = map(y, 0, 480, 0, 180);  // Mappage y aux angles du servo2
  int angle3 = map((int)angle, -90, 90, 0, 180); // Mappage de l'orientation à servo3 (exemple)

  servo1.write(angle1);  // Axe X
  delay(500);
  servo2.write(angle2);  // Axe Y
  delay(500);
  servo3.write(angle3);  // Orientation
  delay(500);

  Serial.print("Déplacement vers X: ");
  Serial.println(angle1);
  Serial.print("Déplacement vers Y: ");
  Serial.println(angle2);
  Serial.print("Orientation (Angle): ");
  Serial.println(angle3);
}

// Fonction pour saisir le tuyau (actionner le gripper)
void grab_pipe() {
  Serial.println("Saisie du tuyau...");
  servo6.write(0);   // Fermer le gripper
  delay(1000);       // Attendre un peu
  servo6.write(90);  // Relâcher le gripper
  Serial.println("Tuyau saisi et relâché.");
}
