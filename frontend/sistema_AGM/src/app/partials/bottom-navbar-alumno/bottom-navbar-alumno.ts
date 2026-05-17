import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';

@Component({
  selector: 'app-bottom-navbar-alumno',
  standalone: true,
  imports: [RouterLink, RouterLinkActive],
  templateUrl: './bottom-navbar-alumno.html',
  styleUrl: './bottom-navbar-alumno.scss'
})
export class BottomNavbarAlumno {}