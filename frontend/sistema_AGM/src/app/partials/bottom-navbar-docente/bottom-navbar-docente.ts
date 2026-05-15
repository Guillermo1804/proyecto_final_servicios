import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';

@Component({
  selector: 'app-bottom-navbar-docente',
  standalone: true,
  imports: [RouterLink, RouterLinkActive],
  templateUrl: './bottom-navbar-docente.html',
  styleUrl: './bottom-navbar-docente.scss'
})
export class BottomNavbarDocente {}